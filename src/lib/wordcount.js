/**
 * 纯函数：字数统计与阅读时长估算。
 * 中文按"字"计，英文/数字按"词"计，标点与空白不计入。
 */

const CJK =
  /[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]/u;
const LATIN_WORD = /[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*/g;

/**
 * 统计文本字数（中文逐字 + 拉丁词）。
 * @param {unknown} text
 * @returns {number}
 */
export function countWords(text) {
  if (typeof text !== 'string' || text.length === 0) return 0;
  let cjk = 0;
  let rest = '';
  for (const ch of text) {
    if (CJK.test(ch)) {
      cjk += 1;
    } else {
      rest += ch;
    }
  }
  const latin = rest.match(LATIN_WORD);
  return cjk + (latin ? latin.length : 0);
}

/**
 * 统计字符数（不含空白字符）。
 * @param {unknown} text
 * @returns {number}
 */
export function countChars(text) {
  if (typeof text !== 'string') return 0;
  return Array.from(text.replace(/\s+/gu, '')).length;
}

/**
 * 阅读时长（分钟，向上取整，最少 1 分钟；0 字返回 0）。
 * @param {number} words
 * @param {number} [wordsPerMinute]
 * @returns {number}
 */
export function readingMinutes(words, wordsPerMinute = 400) {
  const w = Number.isFinite(words) ? Math.max(0, Math.floor(words)) : 0;
  if (w === 0) return 0;
  return Math.max(1, Math.ceil(w / wordsPerMinute));
}

/**
 * 格式化字数：12345 -> "1.2 万字"，860 -> "860 字"。
 * @param {number} words
 * @returns {string}
 */
export function formatWords(words) {
  const w = Number.isFinite(words) ? Math.max(0, Math.round(words)) : 0;
  if (w >= 10000) {
    const v = w / 10000;
    return `${v >= 100 ? Math.round(v) : v.toFixed(1)} 万字`;
  }
  return `${w} 字`;
}

/**
 * 段落拆分，过滤空段。
 * @param {unknown} text
 * @returns {string[]}
 */
export function splitParagraphs(text) {
  if (typeof text !== 'string') return [];
  return text
    .replace(/\r\n/gu, '\n')
    .split(/\n\s*\n/u)
    .map((p) => p.trim())
    .filter((p) => p.length > 0);
}
