/**
 * SQLite 持久层（better-sqlite3）。
 *
 * 设计要点：
 *   1. 同步 API：better-sqlite3 天然同步，Next.js 路由里无需额外 Promise 包装。
 *   2. 单例连接：initDb() 打开（并保证 schema 就绪）唯一连接，getDb() 取用，
 *      closeDb() 关闭并释放；所有调用方共享同一个句柄。
 *   3. 每个连接都开启 PRAGMA journal_mode = WAL 与 PRAGMA foreign_keys = ON。
 *      内存库（:memory:）上 WAL 会自动回退为 memory 模式，属正常现象。
 *   4. schema 使用 CREATE TABLE IF NOT EXISTS，幂等可重复执行。
 *   5. 表结构围绕「书（books）」组织：books / bible / outlines / chapters / llm_logs /
 *      chapter_revisions，子表通过 book_id 外键 ON DELETE CASCADE 随书清理；
 *      chapter_revisions 通过 chapter_id 外键随章节清理。
 */

import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import BetterSqlite3 from 'better-sqlite3';

/** 默认数据库文件路径，可用环境变量 LINGWEN_DB_PATH 覆盖。 */
const DEFAULT_DB_PATH = 'data/lingwen.db';

/** 内存库哨兵值：WAL 在其上不生效，属正常现象。 */
const MEMORY = ':memory:';

/**
 * 建表语句。六张表：
 *   books             —— 书籍主表
 *   bible             —— 设定集（分类条目）
 *   outlines          —— 大纲
 *   chapters          —— 章节（含字数与摘要）
 *   llm_logs          —— 大模型调用日志
 *   chapter_revisions —— 章节版本快照（正文历史）
 */
const SCHEMA = `
CREATE TABLE IF NOT EXISTS books (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT NOT NULL,
  genre       TEXT,
  summary     TEXT,
  style       TEXT,
  created_at  TEXT,
  updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS bible (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id   INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  category  TEXT,
  title     TEXT,
  content   TEXT
);
CREATE INDEX IF NOT EXISTS idx_bible_book ON bible (book_id);

CREATE TABLE IF NOT EXISTS outlines (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id   INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  seq       INTEGER,
  title     TEXT,
  summary   TEXT,
  status    TEXT
);
CREATE INDEX IF NOT EXISTS idx_outlines_book ON outlines (book_id);

CREATE TABLE IF NOT EXISTS chapters (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id     INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  outline_id  INTEGER,
  seq         INTEGER,
  title       TEXT,
  content     TEXT,
  word_count  INTEGER DEFAULT 0,
  summary     TEXT,
  status      TEXT,
  created_at  TEXT,
  updated_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters (book_id);

CREATE TABLE IF NOT EXISTS llm_logs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id     INTEGER,
  kind        TEXT,
  prompt      TEXT,
  response    TEXT,
  elapsed_ms  INTEGER,
  created_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_llm_logs_book ON llm_logs (book_id);

CREATE TABLE IF NOT EXISTS chapter_revisions (
  id          TEXT PRIMARY KEY,
  chapter_id  TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  content     TEXT NOT NULL,
  word_count  INTEGER NOT NULL,
  source      TEXT NOT NULL,
  created_at  TEXT NOT NULL
);

-- 写作会话：每次章节正文净增删一条（book_id / chapter_id 仅作冗余索引，不做外键约束，
-- 以便历史统计在书/章节删除后仍然保留）。
CREATE TABLE IF NOT EXISTS writing_sessions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id     INTEGER,
  chapter_id  INTEGER,
  delta_words INTEGER,
  created_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_writing_sessions_created ON writing_sessions (created_at);
CREATE INDEX IF NOT EXISTS idx_writing_sessions_book ON writing_sessions (book_id);

-- 应用级键值配置（如每日目标 daily_goal），无需预插数据，读取时给默认值。
CREATE TABLE IF NOT EXISTS app_settings (
  key    TEXT PRIMARY KEY,
  value  TEXT
);
`;

/** 当前连接（单例）。@type {import('better-sqlite3').Database | null} */
let connection = null;

/** 当前连接对应的数据库路径（用于判断是否需要重开）。@type {string | null} */
let connectionPath = null;

/**
 * 从参数中解析数据库路径。
 * 允许 initDb()、initDb(path)、initDb({ path })、initDb({ file / filePath / dbPath })。
 * @param {unknown} [input]
 * @returns {string}
 */
function resolvePath(input) {
  let value = input;
  if (value && typeof value === 'object') {
    const obj = /** @type {Record<string, unknown>} */ (value);
    value = obj.path ?? obj.filePath ?? obj.file ?? obj.dbPath;
  }
  if (typeof value === 'string' && value.trim() !== '') return value;
  const fromEnv = process.env.LINGWEN_DB_PATH;
  return typeof fromEnv === 'string' && fromEnv.trim() !== '' ? fromEnv : DEFAULT_DB_PATH;
}

/**
 * 对连接应用必需的 PRAGMA。
 * @param {import('better-sqlite3').Database} db
 */
function applyPragmas(db) {
  // 文件库启用 WAL；内存库上 SQLite 会回退为 memory 模式，不视为错误。
  try {
    db.pragma('journal_mode = WAL');
  } catch {
    // WAL 在某些文件系统上不可用，退回默认模式，不影响功能。
  }
  // 每个连接都必须开启外键约束（SQLite 默认关闭）。
  db.pragma('foreign_keys = ON');
}

/**
 * 建表 / 建索引（幂等）。
 * @param {import('better-sqlite3').Database} db
 */
function migrate(db) {
  db.exec(SCHEMA);
}

/**
 * 打开（或复用）数据库连接，并保证 schema 已就绪。
 * 重复调用且路径一致时返回同一个连接；路径变化时先关闭旧连接。
 * @param {string | { path?: string, filePath?: string, file?: string, dbPath?: string }} [filePath]
 *  数据库文件路径；传 ':memory:' 可得到内存库（测试用）。
 * @returns {import('better-sqlite3').Database}
 */
export function initDb(filePath) {
  const target = resolvePath(filePath);

  if (connection && connection.open && connectionPath === target) {
    migrate(connection);
    return connection;
  }
  if (connection) {
    closeDb();
  }

  if (target !== MEMORY) {
    mkdirSync(dirname(target), { recursive: true });
  }

  const db = new BetterSqlite3(target);
  applyPragmas(db);
  migrate(db);

  connection = db;
  connectionPath = target;
  return db;
}

/**
 * 获取当前连接。
 * 未初始化时抛出清晰错误，提示调用方先执行 initDb()。
 * @returns {import('better-sqlite3').Database}
 */
export function getDb() {
  if (!connection || !connection.open) {
    throw new Error(
      '数据库尚未初始化：请先调用 initDb(path) 打开连接，再使用 getDb()。',
    );
  }
  return connection;
}

/**
 * 关闭连接并清空单例。重复调用是安全的。
 * @returns {void}
 */
export function closeDb() {
  const db = connection;
  connection = null;
  connectionPath = null;
  if (db && db.open) {
    try {
      db.close();
    } catch {
      // 关闭失败（例如仍有未完成语句）不应让调用方崩溃。
    }
  }
}
