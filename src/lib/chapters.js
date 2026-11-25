/**
 * 纯函数：章节排序 / 重排 / 统计。
 */

import { countChars, countWords } from './wordcount.js';

/**
 * @typedef {{ id: string, order: number }} Ordered
 */

/**
 * 按 order 升序稳定排序（order 相同则按原顺序）。
 * @template {Ordered} T
 * @param {T[]} chapters
 * @returns {T[]}
 */
export function sortChapters(chapters) {
  if (!Array.isArray(chapters)) return [];
  return chapters
    .map((chapter, index) => ({ chapter, index }))
    .sort((a, b) => {
      const diff = (a.chapter.order ?? 0) - (b.chapter.order ?? 0);
      return diff !== 0 ? diff : a.index - b.index;
    })
    .map((item) => item.chapter);
}

/**
 * 新章节应使用的 order（追加到末尾）。
 * @param {Ordered[]} chapters
 * @returns {number}
 */
export function nextOrder(chapters) {
  const list = Array.isArray(chapters) ? chapters : [];
  if (list.length === 0) return 1;
  return list.reduce((max, c) => Math.max(max, Number(c.order) || 0), 0) + 1;
}

/**
 * 将 order 重排为 1..n（不修改入参）。
 * @template {Ordered} T
 * @param {T[]} chapters
 * @returns {T[]}
 */
export function reindex(chapters) {
  return sortChapters(chapters).map((chapter, index) => ({
    ...chapter,
    order: index + 1,
  }));
}

/**
 * 上移 / 下移一个章节，返回重排后的完整列表。
 * @template {Ordered} T
 * @param {T[]} chapters
 * @param {string} id
 * @param {'up' | 'down'} direction
 * @returns {T[]}
 */
export function moveChapter(chapters, id, direction) {
  const list = reindex(chapters);
  const index = list.findIndex((c) => c.id === id);
  if (index === -1) return list;
  const target = direction === 'up' ? index - 1 : index + 1;
  if (target < 0 || target >= list.length) return list;
  const copy = list.slice();
  const [item] = copy.splice(index, 1);
  copy.splice(target, 0, item);
  return copy.map((chapter, i) => ({ ...chapter, order: i + 1 }));
}

/**
 * 章节序号标签。
 * @param {number} order
 * @returns {string}
 */
export function chapterLabel(order) {
  const n = Number.isFinite(order) ? Math.trunc(order) : 0;
  return n > 0 ? `第 ${n} 章` : '未命名章节';
}

/**
 * 汇总统计。
 * @param {{ content?: string }[]} chapters
 * @returns {{ chapterCount: number, wordCount: number, charCount: number }}
 */
export function summarizeChapters(chapters) {
  const list = Array.isArray(chapters) ? chapters : [];
  let wordCount = 0;
  let charCount = 0;
  for (const chapter of list) {
    const content = typeof chapter?.content === 'string' ? chapter.content : '';
    wordCount += countWords(content);
    charCount += countChars(content);
  }
  return { chapterCount: list.length, wordCount, charCount };
}
