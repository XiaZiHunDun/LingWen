/**
 * 全书查找替换（book-wide find & replace）。
 *
 * 设计要点：
 *   1. 纯计算 + 持久化分离：
 *        - countOccurrences / buildSnippets / applyReplacement 是**纯函数**，无副作用；
 *        - previewBookReplace 只读（不写库），用于「先预览」；
 *        - replaceBookText 才是写操作，且整体包在 **better-sqlite3 事务**里。
 *   2. 原子性：一次替换 = 一个事务。事务内按章节做两步：
 *        a. 用**替换前**正文写一条 chapter_revisions 历史快照（source = 'manual'，
 *           与手动编辑同口径，复用仓储层既有的来源白名单，不改 repo.js）；
 *        b. UPDATE chapters SET content / word_count / updated_at。
 *      update 影响行数不为 1 即抛出异常；任何异常都会让 better-sqlite3 自动
 *      ROLLBACK，因此正文、字数、快照三者要么全部生效、要么全部不生效。
 *   3. 字数重算走 src/lib/wordcount.js 的 countWords()，与 repo 写入路径同一口径；
 *      快照里的 wordCount 同样用当前正文重算（不信任库里可能过期的旧值）。
 *   4. 不触碰章节的 status / summary / seq / outline_id 等其它字段：换词不改变
 *      「章节是否为空 / 是否定稿」的既有语义，避免影响既有状态机。
 *   5. 匹配口径：区分大小写的**字面量**匹配（非正则），逐个非重叠命中；
 *      query 为空串时一律视为 0 命中，绝不做「空串匹配每处」的危险操作。
 */

import { randomUUID } from 'node:crypto';
import { getDb } from './db.js';
import { countWords } from './wordcount.js';
import { listChapters } from './repo.js';

/** 单个章节预演时最多返回的上下文片段数。 */
const MAX_SNIPPETS = 2;

/** 上下文片段的左右保留字符数。 */
const SNIPPET_RADIUS = 22;

/** 历史快照来源（复用 repo 既有白名单里的 'manual'）。 */
const REVISION_SOURCE = 'manual';

/**
 * 统计 query 在 text 中出现的次数（非重叠、区分大小写、纯字面量）。
 * query 为空串 / 非字符串 / text 非字符串时返回 0。
 * @param {unknown} text
 * @param {unknown} query
 * @returns {number}
 */
export function countOccurrences(text, query) {
  if (typeof text !== 'string' || typeof query !== 'string' || query === '') return 0;
  if (text === '') return 0;
  let count = 0;
  let index = text.indexOf(query);
  while (index !== -1) {
    count += 1;
    index = text.indexOf(query, index + query.length);
  }
  return count;
}

/**
 * 只替换正文中的字面量 query（全部非重叠命中），不做正则解释。
 * @param {unknown} text
 * @param {unknown} query
 * @param {unknown} replacement
 * @returns {string}
 */
export function applyReplacement(text, query, replacement) {
  const source = typeof text === 'string' ? text : '';
  if (typeof query !== 'string' || query === '') return source;
  const next = typeof replacement === 'string' ? replacement : '';
  return source.split(query).join(next);
}

/**
 * 把空白（含换行）压成单个空格，便于在紧凑的行内展示上下文。
 * @param {string} value
 * @returns {string}
 */
function squash(value) {
  return value.replace(/\s+/g, ' ');
}

/**
 * 为一处正文生成若干上下文片段：{ before, match, after }，命中词单独返回便于高亮。
 * 片段两端被裁掉时补省略号「…」。
 * @param {string} content
 * @param {string} query
 * @param {number} [limit] 最多片段数
 * @returns {Array<{ before: string, match: string, after: string }>}
 */
export function buildSnippets(content, query, limit = MAX_SNIPPETS) {
  if (typeof content !== 'string' || typeof query !== 'string' || query === '') return [];
  const snippets = [];
  const max = Number.isInteger(limit) && limit > 0 ? limit : MAX_SNIPPETS;
  let index = content.indexOf(query);
  while (index !== -1 && snippets.length < max) {
    const start = Math.max(0, index - SNIPPET_RADIUS);
    const end = Math.min(content.length, index + query.length + SNIPPET_RADIUS);
    const beforeRaw = squash(content.slice(start, index));
    const afterRaw = squash(content.slice(index + query.length, end));
    snippets.push({
      before: (start > 0 ? '…' : '') + beforeRaw,
      match: query,
      after: afterRaw + (end < content.length ? '…' : ''),
    });
    index = content.indexOf(query, index + query.length);
  }
  return snippets;
}

/**
 * 章节标题兜底（与既有导出逻辑一致：空标题显示「未命名」）。
 * @param {unknown} title
 * @returns {string}
 */
function safeTitle(title) {
  return typeof title === 'string' && title.trim() !== '' ? title : '未命名';
}

/**
 * 预览：全书范围内 query 出现在哪些章节、各命中多少次、上下文片段。
 * 只读，不写任何表。
 * @param {number|string} bookId
 * @param {string} query
 * @returns {{ query: string, totalMatches: number, chapterCount: number,
 *   chapters: Array<{ chapterId: number, seq: number|null, title: string, matches: number,
 *     wordCount: number, snippets: Array<{ before: string, match: string, after: string }> }> }}
 */
export function previewBookReplace(bookId, query) {
  const q = typeof query === 'string' ? query : '';
  const chapters = listChapters(bookId);
  const items = [];
  let totalMatches = 0;

  for (const chapter of chapters) {
    const content = typeof chapter.content === 'string' ? chapter.content : '';
    const matches = countOccurrences(content, q);
    if (matches === 0) continue;
    totalMatches += matches;
    items.push({
      chapterId: Number(chapter.id),
      seq: typeof chapter.seq === 'number' ? chapter.seq : null,
      title: safeTitle(chapter.title),
      matches,
      wordCount: Number(chapter.wordCount ?? 0),
      snippets: buildSnippets(content, q),
    });
  }

  return { query: q, totalMatches, chapterCount: items.length, chapters: items };
}

/**
 * 生成替换计划（纯读取，不写库）：把需要改动的章节与目标正文/字数算出来。
 * @param {number|string} bookId
 * @param {string} query
 * @param {string} replacement
 * @returns {Array<{ chapterId: number, seq: number|null, title: string, matches: number,
 *   content: string, replaced: string, oldWordCount: number, newWordCount: number }>}
 */
function buildPlan(bookId, query, replacement) {
  const plan = [];
  for (const chapter of listChapters(bookId)) {
    const content = typeof chapter.content === 'string' ? chapter.content : '';
    const matches = countOccurrences(content, query);
    if (matches === 0) continue;
    const replaced = applyReplacement(content, query, replacement);
    plan.push({
      chapterId: Number(chapter.id),
      seq: typeof chapter.seq === 'number' ? chapter.seq : null,
      title: safeTitle(chapter.title),
      matches,
      content,
      replaced,
      oldWordCount: countWords(content),
      newWordCount: countWords(replaced),
    });
  }
  return plan;
}

/**
 * 全书替换：原子地把 query 全部换成 replacement。
 *
 * 事务内对每个命中章节先写历史快照（旧正文），再更新正文 + 重算 word_count +
 * 刷新 updated_at；任一步抛错则整个事务回滚，正文/字数/快照保持一致。
 *
 * @param {number|string} bookId
 * @param {{ query?: string, replacement?: string, onChapterUpdated?: (item: {
 *   chapterId: number, seq: number|null, title: string, matches: number,
 *   newWordCount: number, oldWordCount: number }) => void }} [options]
 *   onChapterUpdated：每成功更新一章后调用（事务内）。抛错即触发整体回滚，
 *   测试用它模拟中途异常；生产路径一般不需要。
 * @returns {{ query: string, replacement: string, totalMatches: number, chapterCount: number,
 *   wordCountDelta: number, message: string,
 *   chapters: Array<{ chapterId: number, seq: number|null, title: string, matches: number,
 *     wordCount: number, oldWordCount: number }> }}
 * @throws {RangeError} query 为空时
 */
export function replaceBookText(bookId, { query, replacement = '', onChapterUpdated } = {}) {
  const q = typeof query === 'string' ? query : '';
  const next = typeof replacement === 'string' ? replacement : '';
  if (q === '') throw new RangeError('查找词不能为空');
  if (q === next) throw new RangeError('新词与查找词相同，无需替换');

  const db = getDb();
  const plan = buildPlan(bookId, q, next);

  if (plan.length === 0) {
    return {
      query: q,
      replacement: next,
      totalMatches: 0,
      chapterCount: 0,
      wordCountDelta: 0,
      message: '共替换 0 处，涉及 0 章',
      chapters: [],
    };
  }

  const insertRevision = db.prepare(
    `INSERT INTO chapter_revisions (id, chapter_id, content, word_count, source, created_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'))`,
  );
  const updateChapterStmt = db.prepare(
    `UPDATE chapters
        SET content = ?, word_count = ?, updated_at = datetime('now')
      WHERE id = ?`,
  );

  // 单一事务：所有章节的快照 + 正文更新同生共死。
  const apply = db.transaction((items) => {
    const applied = [];
    for (const item of items) {
      // 1) 历史版本快照：存「替换前」正文，字数按旧正文重算。
      insertRevision.run(
        randomUUID(),
        item.chapterId,
        item.content,
        item.oldWordCount,
        REVISION_SOURCE,
      );
      // 2) 正文 + 字数 + updated_at 一起更新；影响行数异常视为致命错误。
      const info = updateChapterStmt.run(item.replaced, item.newWordCount, item.chapterId);
      if (!info || info.changes !== 1) {
        throw new Error(`章节 ${item.chapterId} 更新失败，已回滚本次全书替换`);
      }
      applied.push(item);
      if (typeof onChapterUpdated === 'function') {
        onChapterUpdated({
          chapterId: item.chapterId,
          seq: item.seq,
          title: item.title,
          matches: item.matches,
          oldWordCount: item.oldWordCount,
          newWordCount: item.newWordCount,
        });
      }
    }
    return applied;
  });

  const applied = apply(plan);
  const totalMatches = applied.reduce((sum, item) => sum + item.matches, 0);
  const wordCountDelta = applied.reduce(
    (sum, item) => sum + (item.newWordCount - item.oldWordCount),
    0,
  );

  return {
    query: q,
    replacement: next,
    totalMatches,
    chapterCount: applied.length,
    wordCountDelta,
    message: `共替换 ${totalMatches} 处，涉及 ${applied.length} 章`,
    chapters: applied.map((item) => ({
      chapterId: item.chapterId,
      seq: item.seq,
      title: item.title,
      matches: item.matches,
      wordCount: item.newWordCount,
      oldWordCount: item.oldWordCount,
    })),
  };
}
