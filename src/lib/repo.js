/**
 * 数据访问层（repository）：对 SQLite 六张表做最小可用的 CRUD 封装。
 *
 * 设计要点：
 *   1. 连接惰性获取：模块顶层**不**调用 getDb()，因为导入本模块时数据库可能尚未
 *      initDb()，顶层取连接会抛错。所有函数内部才调用 getDb()，因此 stmt 也只能
 *      在函数内 prepare（或按 db 实例做惰性缓存），不能写成模块级常量。
 *   2. 全部使用 better-sqlite3 的 prepare + 参数化（? 占位符），SQL 中出现的值一律
 *      走参数绑定；动态部分（如 UPDATE 的 SET 子句）只拼接「白名单列名」，绝不拼接值。
 *   3. 行对象统一转 camelCase 后返回：book_id→bookId、outline_id→outlineId、
 *      word_count→wordCount、elapsed_ms→elapsedMs、created_at→createdAt、
 *      updated_at→updatedAt、chapter_id→chapterId。写入方向则做反向映射。
 *   4. 时间戳统一由 SQLite 的 datetime('now') 生成（UTC，'YYYY-MM-DD HH:MM:SS'）。
 *   5. 约定：getBook / getChapter / getChapterRevision 查不到时返回 undefined
 *      （即 Statement#get 的原始结果）。
 */

import { randomUUID } from 'node:crypto';
import { getDb } from './db.js';
import { countWords } from './wordcount.js';

/**
 * snake_case → camelCase 的列名映射表。
 * 未列出的列名（id / title / genre / summary / style / content / status / seq /
 * category / kind / prompt / response / source）在两种风格下拼写一致，直接透传。
 * @type {Record<string, string>}
 */
const COLUMN_TO_FIELD = {
  book_id: 'bookId',
  outline_id: 'outlineId',
  chapter_id: 'chapterId',
  word_count: 'wordCount',
  elapsed_ms: 'elapsedMs',
  created_at: 'createdAt',
  updated_at: 'updatedAt',
};

/** camelCase → snake_case 的反向映射（写入方向使用）。 */
const FIELD_TO_COLUMN = Object.fromEntries(
  Object.entries(COLUMN_TO_FIELD).map(([column, field]) => [field, column]),
);

/**
 * 把数据库行对象转成 camelCase 行对象；null/undefined 原样返回。
 * @param {Record<string, unknown> | null | undefined} row
 * @returns {Record<string, unknown> | undefined}
 */
function mapRow(row) {
  if (!row) return undefined;
  /** @type {Record<string, unknown>} */
  const out = {};
  for (const [key, value] of Object.entries(row)) {
    out[COLUMN_TO_FIELD[key] ?? key] = value;
  }
  return out;
}

/**
 * 批量转换行数组。
 * @param {Array<Record<string, unknown>>} rows
 * @returns {Array<Record<string, unknown>>}
 */
function mapRows(rows) {
  return rows.map((row) => mapRow(row));
}

/**
 * 把 patch 对象的键翻译为列名，并只保留 allowed 白名单内的字段。
 * 返回 [列名数组, 值数组]，顺序一致，供 SET 子句与参数绑定使用。
 * @param {Record<string, unknown>} patch
 * @param {string[]} allowed 允许更新的 camelCase 字段名
 * @returns {{ columns: string[], values: unknown[] }}
 */
function pickColumns(patch, allowed) {
  const columns = [];
  const values = [];
  for (const field of allowed) {
    if (patch && Object.prototype.hasOwnProperty.call(patch, field) && patch[field] !== undefined) {
      columns.push(FIELD_TO_COLUMN[field] ?? field);
      values.push(/** @type {unknown} */ (patch[field]));
    }
  }
  return { columns, values };
}

/**
 * 新建一本书。
 * @param {{ title: string, genre?: string|null, summary?: string|null, style?: string|null }} input
 * @returns {Record<string, unknown>} 新建的 camelCase book 行
 */
export function createBook({ title, genre = null, summary = null, style = null }) {
  const db = getDb();
  const info = db
    .prepare(
      `INSERT INTO books (title, genre, summary, style, created_at, updated_at)
       VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))`,
    )
    .run(title, genre, summary, style);
  const row = db.prepare('SELECT * FROM books WHERE id = ?').get(info.lastInsertRowid);
  return mapRow(row);
}

/**
 * 列出全部书籍，按 id 升序。
 * @returns {Array<Record<string, unknown>>}
 */
export function listBooks() {
  const db = getDb();
  return mapRows(db.prepare('SELECT * FROM books ORDER BY id ASC').all());
}

/**
 * 按 id 取单本书。
 * @param {number} id
 * @returns {Record<string, unknown> | undefined} 不存在时返回 undefined
 */
export function getBook(id) {
  const db = getDb();
  return mapRow(db.prepare('SELECT * FROM books WHERE id = ?').get(id));
}

/**
 * 局部更新一本书：只更新 patch 中出现的 title/genre/summary/style，
 * 并始终刷新 updated_at = datetime('now')。
 * @param {number} id
 * @param {{ title?: string, genre?: string|null, summary?: string|null, style?: string|null }} patch
 * @returns {Record<string, unknown> | undefined} 更新后的 camelCase 行
 */
export function updateBook(id, patch) {
  const db = getDb();
  const { columns, values } = pickColumns(patch ?? {}, ['title', 'genre', 'summary', 'style']);
  // 动态部分只有列名（来自固定白名单），值仍是占位符绑定。
  const assignments = columns.map((column) => `${column} = ?`);
  assignments.push("updated_at = datetime('now')");
  db.prepare(`UPDATE books SET ${assignments.join(', ')} WHERE id = ?`).run(...values, id);
  return mapRow(db.prepare('SELECT * FROM books WHERE id = ?').get(id));
}

/**
 * 列出某本书的全部设定集条目（按 id 升序）。
 * @param {number} bookId
 * @returns {Array<Record<string, unknown>>}
 */
export function listBible(bookId) {
  const db = getDb();
  return mapRows(
    db.prepare('SELECT * FROM bible WHERE book_id = ? ORDER BY id ASC').all(bookId),
  );
}

/**
 * 新增一条设定集条目。
 *
 * 签名说明：采用**单个对象参数**（{ bookId, category, title, content }），
 * 与 createBook / createChapter / logLlm 保持一致，避免位置参数顺序出错。
 * @param {{ bookId: number, category?: string|null, title?: string|null, content?: string|null }} input
 * @returns {Record<string, unknown>} 新增的 camelCase 行
 */
export function addBible({ bookId, category = null, title = null, content = null }) {
  const db = getDb();
  const info = db
    .prepare('INSERT INTO bible (book_id, category, title, content) VALUES (?, ?, ?, ?)')
    .run(bookId, category, title, content);
  return mapRow(db.prepare('SELECT * FROM bible WHERE id = ?').get(info.lastInsertRowid));
}

/**
 * 删除一条设定集条目。
 * @param {number} id
 * @returns {number} 被删除的行数（0 表示该 id 不存在）
 */
export function deleteBible(id) {
  const db = getDb();
  return db.prepare('DELETE FROM bible WHERE id = ?').run(id).changes;
}

/**
 * 整体替换某本书的大纲：在同一事务中先 DELETE 该书全部 outlines，再批量插入。
 * @param {number} bookId
 * @param {Array<{ seq?: number|null, title?: string|null, summary?: string|null, status?: string|null }>} outlines
 * @returns {Array<Record<string, unknown>>} 插入后该书的大纲（按 seq 升序）
 */
export function replaceOutlines(bookId, outlines = []) {
  const db = getDb();
  const insert = db.prepare(
    'INSERT INTO outlines (book_id, seq, title, summary, status) VALUES (?, ?, ?, ?, ?)',
  );
  const replace = db.transaction((list) => {
    db.prepare('DELETE FROM outlines WHERE book_id = ?').run(bookId);
    for (const item of list) {
      insert.run(
        bookId,
        item?.seq ?? null,
        item?.title ?? null,
        item?.summary ?? null,
        item?.status ?? null,
      );
    }
  });
  replace(Array.isArray(outlines) ? outlines : []);
  return listOutlines(bookId);
}

/**
 * 列出某本书的大纲，按 seq 升序。
 * @param {number} bookId
 * @returns {Array<Record<string, unknown>>}
 */
export function listOutlines(bookId) {
  const db = getDb();
  return mapRows(
    db.prepare('SELECT * FROM outlines WHERE book_id = ? ORDER BY seq ASC, id ASC').all(bookId),
  );
}

/**
 * 新建一个章节。word_count 由表定义默认 0；created_at / updated_at 用 datetime('now')。
 * @param {{ bookId: number, outlineId?: number|null, seq?: number|null, title?: string|null,
 *   content?: string|null, summary?: string|null, status?: string|null }} input
 * @returns {Record<string, unknown>} 新建的 camelCase 行
 */
export function createChapter({
  bookId,
  outlineId = null,
  seq = null,
  title = null,
  content = null,
  summary = null,
  status = null,
}) {
  const db = getDb();
  const info = db
    .prepare(
      `INSERT INTO chapters
         (book_id, outline_id, seq, title, content, summary, status, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))`,
    )
    .run(bookId, outlineId, seq, title, content, summary, status);
  return mapRow(db.prepare('SELECT * FROM chapters WHERE id = ?').get(info.lastInsertRowid));
}

/**
 * 列出某本书的章节，按 seq 升序。
 * @param {number} bookId
 * @returns {Array<Record<string, unknown>>}
 */
export function listChapters(bookId) {
  const db = getDb();
  return mapRows(
    db.prepare('SELECT * FROM chapters WHERE book_id = ? ORDER BY seq ASC, id ASC').all(bookId),
  );
}

/**
 * 按 id 取单个章节。
 * @param {number} id
 * @returns {Record<string, unknown> | undefined} 不存在时返回 undefined
 */
export function getChapter(id) {
  const db = getDb();
  return mapRow(db.prepare('SELECT * FROM chapters WHERE id = ?').get(id));
}

/**
 * 局部更新章节：只更新 patch 中出现的
 * outlineId / seq / title / content / summary / status / wordCount，
 * 并始终刷新 updated_at = datetime('now')。
 * @param {number} id
 * @param {{ outlineId?: number|null, seq?: number|null, title?: string|null,
 *   content?: string|null, summary?: string|null, status?: string|null,
 *   wordCount?: number|null }} patch
 * @returns {Record<string, unknown> | undefined} 更新后的 camelCase 行
 */
export function updateChapter(id, patch) {
  const db = getDb();
  const { columns, values } = pickColumns(patch ?? {}, [
    'outlineId',
    'seq',
    'title',
    'content',
    'summary',
    'status',
    'wordCount',
  ]);
  const assignments = columns.map((column) => `${column} = ?`);
  assignments.push("updated_at = datetime('now')");
  db.prepare(`UPDATE chapters SET ${assignments.join(', ')} WHERE id = ?`).run(...values, id);
  return mapRow(db.prepare('SELECT * FROM chapters WHERE id = ?').get(id));
}

/**
 * 记录一次大模型调用日志。created_at 用 datetime('now')。
 * @param {{ bookId?: number|null, kind?: string|null, prompt?: string|null,
 *   response?: string|null, elapsedMs?: number|null }} input
 * @returns {{ id: number }} 插入行的 id（需要整行时用 getLlmLog 语义自行查询）
 */
export function logLlm({ bookId = null, kind = null, prompt = null, response = null, elapsedMs = null }) {
  const db = getDb();
  const info = db
    .prepare(
      `INSERT INTO llm_logs (book_id, kind, prompt, response, elapsed_ms, created_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))`,
    )
    .run(bookId, kind, prompt, response, elapsedMs);
  return { id: Number(info.lastInsertRowid) };
}

/* ------------------------------------------------------------------ *
 * 章节版本快照（chapter_revisions）
 * ------------------------------------------------------------------ */

/** 版本来源白名单。 */
export const CHAPTER_REVISION_SOURCES = ['manual', 'generate', 'restore', 'pre-restore'];

/** 列表预览长度（字符）。 */
const PREVIEW_LENGTH = 80;

/**
 * 校验版本来源，非法值直接抛错（避免脏数据入库）。
 * @param {unknown} source
 * @returns {string}
 */
function assertRevisionSource(source) {
  if (typeof source !== 'string' || !CHAPTER_REVISION_SOURCES.includes(source)) {
    throw new Error(
      `非法的版本来源：${String(source)}（仅允许 ${CHAPTER_REVISION_SOURCES.join(' / ')}）`,
    );
  }
  return source;
}

/**
 * 生成正文预览：先压缩空白（含换行）为单个空格，再取前 80 字。
 * @param {string} content
 * @returns {string}
 */
function buildPreview(content) {
  return content.replace(/\s+/g, ' ').trim().slice(0, PREVIEW_LENGTH);
}

/**
 * 新增一条章节版本快照。
 * word_count 由正文自动计算；created_at 用 datetime('now')；id 用 UUID。
 * @param {{ chapterId: number|string, content: string, source: string }} input
 * @returns {Record<string, unknown>} 新建的 camelCase 行（含全文 content）
 */
export function createChapterRevision({ chapterId, content, source }) {
  const safeSource = assertRevisionSource(source);
  const text = typeof content === 'string' ? content : '';
  const db = getDb();
  const id = randomUUID();
  db.prepare(
    `INSERT INTO chapter_revisions (id, chapter_id, content, word_count, source, created_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'))`,
  ).run(id, chapterId, text, countWords(text), safeSource);
  return mapRow(db.prepare('SELECT * FROM chapter_revisions WHERE id = ?').get(id));
}

/**
 * 列出某章节的版本快照（按时间倒序，最新在前）。
 * 只返回 id / source / wordCount / createdAt / preview，不带全文。
 * @param {number|string} chapterId
 * @returns {Array<{ id: string, source: string, wordCount: number, createdAt: string, preview: string }>}
 */
export function listChapterRevisions(chapterId) {
  const db = getDb();
  const rows = /** @type {Array<Record<string, unknown>>} */ (
    db
      .prepare(
        `SELECT id, source, word_count, created_at, content
           FROM chapter_revisions
          WHERE chapter_id = ?
          ORDER BY created_at DESC, rowid DESC`,
      )
      .all(chapterId)
  );
  return rows.map((row) => {
    const content = typeof row.content === 'string' ? row.content : '';
    return {
      id: String(row.id),
      source: String(row.source),
      wordCount: Number(row.word_count ?? 0),
      createdAt: String(row.created_at ?? ''),
      preview: buildPreview(content),
    };
  });
}

/**
 * 按 id 取单条版本快照（含全文）。
 * @param {string} id
 * @returns {Record<string, unknown> | undefined} 不存在时返回 undefined
 */
export function getChapterRevision(id) {
  const db = getDb();
  return mapRow(db.prepare('SELECT * FROM chapter_revisions WHERE id = ?').get(id));
}

/**
 * 把某个历史版本写回章节正文。
 * 注意：调用方应在此前先存一条 source='pre-restore' 的快照（本函数不做该步骤）。
 * @param {string} id 版本快照 id
 * @returns {Record<string, unknown> | undefined} 恢复后的 camelCase chapter 行；
 *   版本不存在时返回 undefined
 */
export function restoreChapterRevision(id) {
  const revision = getChapterRevision(id);
  if (revision === undefined) return undefined;
  const chapterId = revision.chapterId;
  if (chapterId === undefined || chapterId === null) return undefined;
  const content = typeof revision.content === 'string' ? revision.content : '';
  const wordCount =
    typeof revision.wordCount === 'number' ? revision.wordCount : countWords(content);
  const db = getDb();
  db.prepare(
    `UPDATE chapters SET content = ?, word_count = ?, updated_at = datetime('now') WHERE id = ?`,
  ).run(content, wordCount, chapterId);
  return mapRow(db.prepare('SELECT * FROM chapters WHERE id = ?').get(chapterId));
}

/**
 * 裁剪某章节的版本快照：按时间倒序只保留最近 keep 条，其余删除。
 * @param {number|string} chapterId
 * @param {number} [keep] 保留条数，默认 20（小于 1 时按 1 处理）
 * @returns {number} 被删除的条数
 */
export function pruneChapterRevisions(chapterId, keep = 20) {
  const limit = Number.isFinite(keep) ? Math.max(1, Math.floor(keep)) : 20;
  const db = getDb();
  const info = db
    .prepare(
      `DELETE FROM chapter_revisions
        WHERE chapter_id = ?
          AND id NOT IN (
            SELECT id FROM chapter_revisions
             WHERE chapter_id = ?
             ORDER BY created_at DESC, rowid DESC
             LIMIT ?
          )`,
    )
    .run(chapterId, chapterId, limit);
  return info.changes;
}
