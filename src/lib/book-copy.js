/**
 * 复制作品（duplicate book）：命名规则纯函数 + 仓储层复制逻辑。
 *
 * 设计要点：
 *   1. generateCopyName 是纯函数（无 IO、无数据库依赖），便于单测；
 *   2. duplicateBook 只调用 repo 现有的建行函数（createBook / createChapter /
 *      addBible / replaceOutlines），不写裸 SQL（除读取已有书名做重名判断）；
 *   3. 字数口径与整书导入 / 导出保持一致：一律复用 countWords(content)；
 *   4. 不复制章节历史版本（chapter_revisions）、写作会话（writing_sessions）、
 *      LLM 调用日志（llm_logs）——这三者属于原书的创作过程痕迹；
 *   5. 找不到原书时抛 NotFoundError（code = 'NOT_FOUND'），路由层据此返回 404。
 */

import { getDb } from './db.js';
import {
  addBible,
  createBook,
  createChapter,
  getBook,
  listBible,
  listChapters,
  listOutlines,
  replaceOutlines,
} from './repo.js';
import { countWords } from './wordcount.js';

/** 首个副本使用的后缀。 */
export const COPY_SUFFIX = '（副本）';

/** 空书名兜底（books.title 为 NOT NULL，复制时不允许写入空串）。 */
const FALLBACK_TITLE = '未命名作品';

/**
 * 资源不存在的可识别错误。
 * 路由层用 `error instanceof NotFoundError`（或 error.code）判断后返回 404。
 */
export class NotFoundError extends Error {
  /**
   * @param {string} message
   */
  constructor(message) {
    super(message);
    this.name = 'NotFoundError';
    this.code = 'NOT_FOUND';
  }
}

/**
 * 生成一个不与 existingNames 冲突的副本名。
 *
 * 规则：
 *   - 首个副本：`原书名（副本）`
 *   - 若已存在同名副本：依次尝试 `原书名（副本 2）`、`原书名（副本 3）` …
 *   - 返回值一定不在 existingNames 中（比较前做 trim，忽略空串）。
 *
 * @param {string} baseName 原书名
 * @param {Array<string | null | undefined> | Iterable<string | null | undefined>} [existingNames]
 *   已存在的书名集合（同作者或全表均可）；不传按空集合处理
 * @returns {string} 新书名
 */
export function generateCopyName(baseName, existingNames = []) {
  const base =
    typeof baseName === 'string' && baseName.trim() !== '' ? baseName.trim() : FALLBACK_TITLE;

  /** @type {Set<string>} */
  const used = new Set();
  const list = existingNames ?? [];
  for (const name of list) {
    if (typeof name === 'string' && name.trim() !== '') used.add(name.trim());
  }

  const first = `${base}${COPY_SUFFIX}`;
  if (!used.has(first)) return first;

  // 理论上不会跑满；上限只是防御性兜底，避免极端情况下死循环。
  for (let n = 2; n <= 10000; n += 1) {
    const candidate = `${base}（副本 ${n}）`;
    if (!used.has(candidate)) return candidate;
  }
  throw new Error(`无法为《${base}》生成不重复的副本名（已尝试到副本 10000）`);
}

/**
 * 复制一整本书：书名按命名规则重新生成，其余内容原样复制。
 *
 * 单事务内依次完成：
 *   1. 取原书（不存在 → NotFoundError）；查询全表已有书名，生成不重复副本名；
 *   2. createBook 复制 genre / summary / style，写入新书名；
 *   3. replaceOutlines 复制全部大纲（seq / title / summary / status），
 *      并按插入顺序建立「原大纲 id → 新大纲 id」映射，供章节 outline_id 重挂；
 *   4. addBible 复制全部设定集条目（category / title / content）；
 *   5. createChapter 复制全部章节：seq / title / content / summary / status 原样保留，
 *      word_count 用 countWords(content) 重新落库（与统计页 / 导出同口径）。
 *
 * 不复制：chapter_revisions / writing_sessions / llm_logs。
 *
 * @param {number} bookId 原书 id
 * @returns {{ id: number, title: string, chapters: number, outlines: number, bible: number }}
 *   新书 id 与各类内容的复制条数
 * @throws {NotFoundError} 原书不存在
 */
export function duplicateBook(bookId) {
  const db = getDb();
  const id = Number(bookId);

  const run = db.transaction((sourceId) => {
    const source = getBook(sourceId);
    if (source === undefined) {
      throw new NotFoundError(`书籍不存在：${sourceId}`);
    }

    // 本表没有作者字段，因此用全表书名做重名判断（同作者在单表场景下等价于全表）。
    const existingNames = db
      .prepare('SELECT title FROM books')
      .all()
      .map((row) => row.title);
    const title = generateCopyName(
      typeof source.title === 'string' ? source.title : '',
      existingNames,
    );

    const book = createBook({
      title,
      genre: typeof source.genre === 'string' ? source.genre : null,
      summary: typeof source.summary === 'string' ? source.summary : null,
      style: typeof source.style === 'string' ? source.style : null,
    });
    const newBookId = Number(book.id);

    const outlines = listOutlines(sourceId);
    const newOutlines = replaceOutlines(
      newBookId,
      outlines.map((outline) => ({
        seq: outline.seq ?? null,
        title: outline.title ?? null,
        summary: outline.summary ?? null,
        status: outline.status ?? null,
      })),
    );
    /** @type {Map<number, number>} */
    const outlineIdMap = new Map();
    outlines.forEach((outline, index) => {
      const created = newOutlines[index];
      if (created !== undefined) {
        outlineIdMap.set(Number(outline.id), Number(created.id));
      }
    });

    const bibleItems = listBible(sourceId);
    for (const item of bibleItems) {
      addBible({
        bookId: newBookId,
        category: item.category ?? null,
        title: item.title ?? null,
        content: item.content ?? null,
      });
    }

    const chapters = listChapters(sourceId);
    for (const chapter of chapters) {
      const content = typeof chapter.content === 'string' ? chapter.content : '';
      createChapter({
        bookId: newBookId,
        outlineId: outlineIdMap.get(Number(chapter.outlineId)) ?? null,
        seq: chapter.seq ?? null,
        title: chapter.title ?? null,
        content: typeof chapter.content === 'string' ? chapter.content : null,
        summary: chapter.summary ?? null,
        status: chapter.status ?? null,
        wordCount: countWords(content),
      });
    }

    return {
      id: newBookId,
      title,
      chapters: chapters.length,
      outlines: newOutlines.length,
      bible: bibleItems.length,
    };
  });

  return run(id);
}
