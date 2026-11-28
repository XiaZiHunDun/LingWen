/**
 * 设定覆盖体检（bible coverage）：纯函数，不碰数据库、不做任何 IO。
 *
 * 口径：
 *   1. 每条设定用 title（trim 后）做**字面量**匹配，区分大小写、逐个非重叠命中，
 *      与全书查找替换同一口径 —— 命中统计直接复用 find-replace.js 的
 *      countOccurrences()，不重写任何匹配逻辑，也不改它的行为。
 *   2. 检索范围：chapters.content、chapters.title、outlines.title、outlines.summary，
 *      四者命中之总和即 occurrences。
 *   3. chapterCount = 至少命中一次的章节数（正文或标题命中都算该章命中）；
 *      outlineCount = 至少命中一次的大纲条数（标题或摘要命中都算该条命中）。
 *   4. title trim 后为空 / 非字符串的设定直接跳过，且不计入 total。
 *   5. 排序：occurrences 升序（从未使用的排最前），同分按 title 升序，稳定排序。
 */

import { countOccurrences } from './find-replace.js';

/**
 * 安全取文本：非字符串一律按空串处理，避免把 undefined 传给 countOccurrences。
 * @param {unknown} value
 * @returns {string}
 */
function text(value) {
  return typeof value === 'string' ? value : '';
}

/**
 * 统计设定在正文 / 章节标题 / 大纲标题 / 大纲摘要里的覆盖情况。
 *
 * @param {{ bible?: unknown[], chapters?: unknown[], outlines?: unknown[] }} [input]
 * @returns {{ items: Array<{ id: unknown, title: string, category: string,
 *   occurrences: number, chapterCount: number, outlineCount: number }>,
 *   total: number, usedCount: number, unusedCount: number }}
 */
export function summarizeBibleCoverage({ bible, chapters, outlines } = {}) {
  const bibleList = Array.isArray(bible) ? bible : [];
  const chapterList = Array.isArray(chapters) ? chapters : [];
  const outlineList = Array.isArray(outlines) ? outlines : [];

  const items = [];

  for (const entry of bibleList) {
    if (typeof entry !== 'object' || entry === null) continue;
    const rawTitle = /** @type {{ title?: unknown }} */ (entry).title;
    if (typeof rawTitle !== 'string') continue;
    const title = rawTitle.trim();
    if (title === '') continue;

    let occurrences = 0;
    let chapterCount = 0;
    let outlineCount = 0;

    for (const chapter of chapterList) {
      if (typeof chapter !== 'object' || chapter === null) continue;
      const content = text(/** @type {{ content?: unknown }} */ (chapter).content);
      const chapterTitle = text(/** @type {{ title?: unknown }} */ (chapter).title);
      const hits = countOccurrences(content, title) + countOccurrences(chapterTitle, title);
      if (hits > 0) {
        chapterCount += 1;
        occurrences += hits;
      }
    }

    for (const outline of outlineList) {
      if (typeof outline !== 'object' || outline === null) continue;
      const outlineTitle = text(/** @type {{ title?: unknown }} */ (outline).title);
      const summary = text(/** @type {{ summary?: unknown }} */ (outline).summary);
      const hits = countOccurrences(outlineTitle, title) + countOccurrences(summary, title);
      if (hits > 0) {
        outlineCount += 1;
        occurrences += hits;
      }
    }

    const source = /** @type {{ id?: unknown, category?: unknown }} */ (entry);
    const category = typeof source.category === 'string' ? source.category : '';

    items.push({
      id: source.id,
      title,
      category,
      occurrences,
      chapterCount,
      outlineCount,
    });
  }

  // 稳定排序：未使用（occurrences 最小）在前，同分按标题升序。
  items.sort((a, b) => {
    if (a.occurrences !== b.occurrences) return a.occurrences - b.occurrences;
    if (a.title === b.title) return 0;
    return a.title < b.title ? -1 : 1;
  });

  const total = items.length;
  let usedCount = 0;
  for (const item of items) {
    if (item.occurrences > 0) usedCount += 1;
  }

  return { items, total, usedCount, unusedCount: total - usedCount };
}
