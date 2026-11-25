/**
 * 纯函数：大纲文本解析与生成。
 * 支持的输入形态（混排亦可）：
 *   1. 章名 —— 摘要
 *   ## 章名 / 第三章 章名
 *   - 章名：摘要
 */

/**
 * @typedef {{ title: string, summary: string }} OutlineItem
 */

const HEADING = /^\s{0,3}#{1,6}\s*(.+?)\s*$/u;
const NUMBERED = /^\s*(?:\d{1,3}|[一二三四五六七八九十百]{1,4})\s*[.、)）]\s*(.+?)\s*$/u;
const BULLET = /^\s*[-*+]\s+(.+?)\s*$/u;
const CN_CHAPTER = /^\s*第\s*[一二三四五六七八九十百千万\d]+\s*[章回节卷]\s*(.*)$/u;
const SPLITTER = /\s*(?:——|—|--|：|:|\||｜)\s*/u;

/**
 * 清洗标题两侧的装饰字符。
 * @param {string} raw
 * @returns {string}
 */
function cleanTitle(raw) {
  return String(raw)
    .replace(/^[`*_~\s]+/u, '')
    .replace(/[`*_~\s]+$/u, '')
    .replace(/^["'“”「」]+|["'“”「」]+$/gu, '')
    .trim();
}

/**
 * 解析一行。
 * @param {string} line
 * @returns {{ title: string, summary: string } | null}
 */
function parseLine(line) {
  const text = line.trim();
  if (!text) return null;

  let rest = null;
  const chapter = text.match(CN_CHAPTER);
  if (chapter) {
    rest = chapter[1] && chapter[1].trim() ? chapter[1] : '新章节';
    const original = cleanTitle(text);
    const [head, ...tail] = original.split(SPLITTER);
    const summary = tail.length > 0 ? cleanTitle(tail.join(' ')) : '';
    return { title: cleanTitle(head) || rest, summary };
  }

  const heading = text.match(HEADING);
  if (heading) rest = heading[1];
  if (!rest) {
    const numbered = text.match(NUMBERED);
    if (numbered) rest = numbered[1];
  }
  if (!rest) {
    const bullet = text.match(BULLET);
    if (bullet) rest = bullet[1];
  }
  if (!rest) return null;

  const [head, ...tail] = rest.split(SPLITTER);
  return {
    title: cleanTitle(head),
    summary: cleanTitle(tail.join(' ')),
  };
}

/**
 * 把任意文本解析为大纲条目。
 * @param {unknown} markdown
 * @returns {OutlineItem[]}
 */
export function parseOutline(markdown) {
  if (typeof markdown !== 'string' || markdown.trim() === '') return [];
  /** @type {OutlineItem[]} */
  const items = [];
  const lines = markdown.replace(/\r\n/gu, '\n').split('\n');
  for (const line of lines) {
    const parsed = parseLine(line);
    if (!parsed) continue;
    if (!parsed.title) continue;
    // 摘要可能折行在后续普通段落里，这里只处理行内摘要。
    if (items.length > 0 && items[items.length - 1].title === parsed.title) {
      if (!items[items.length - 1].summary && parsed.summary) {
        items[items.length - 1].summary = parsed.summary;
      }
      continue;
    }
    items.push(parsed);
  }
  return items;
}

/**
 * 把解析结果转成可读的 Markdown（用于导出/回填）。
 * @param {OutlineItem[]} items
 * @returns {string}
 */
export function outlineToMarkdown(items) {
  const list = Array.isArray(items) ? items : [];
  return list
    .map((item, index) => {
      const suffix = item.summary ? ` —— ${item.summary}` : '';
      return `${index + 1}. ${item.title}${suffix}`;
    })
    .join('\n');
}
