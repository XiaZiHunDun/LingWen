/**
 * Markdown 导入的纯函数实现（无数据库依赖、无文件 IO、不读环境变量）。
 *
 * 解析口径与 src/lib/book-export.js 的 md 产物严格对齐，保证「导出 → 导入」可往返：
 *   1. 末尾 `---` + 空行 + `共 N 章，总字数 M 字。` 的统计段会被整体丢弃，
 *      不会变成最后一章的正文；
 *   2. `## 第 N 章 标题` 形式的章标题会剥掉 `第 N 章 ` 前缀，只留 `标题`；
 *   3. 正文用 unescapeMarkdownBody 反转义，它是 escapeMarkdownBody 的逆函数
 *      （`unescapeMarkdownBody(escapeMarkdownBody(x)) === x`），因此往返后
 *      每章正文与原始 content 完全一致，字数自然也不漂。
 *
 * 空结构约定（测试中已覆盖）：
 *   - 空文件 / 只有 `# 书名` 且没有正文 → 返回 0 章（chapters 为空数组），
 *     书名兜底「未命名」（有 `# 书名` 时取该标题）；
 *   - 有正文但整篇没有二级标题 → 只有 1 章，章标题用书名；
 *   - 正文里三级及以下标题（`### `…）不是章节分隔符，原样保留进 content。
 *
 * 已知取舍（不影响导出产物往返）：
 *   - 章正文首尾的空行会被裁掉（正常正文不会以空行开头/结尾）；
 *   - 第一个 `## ` 之前的非空内容（导出格式里只会有书籍级信息）会被忽略。
 */

import { countWords } from './wordcount.js';

/** 书名兜底文案。 */
export const FALLBACK_BOOK_TITLE = '未命名';

/** 章标题兜底文案。 */
export const FALLBACK_CHAPTER_TITLE = '未命名章节';

/** 一级标题行：`#` + 空白 + 标题（`##` 不会命中，因为第三个字符必须是空白）。 */
const HEADING_LEVEL_1 = /^#[ \t]+(.*)$/u;

/** 二级标题行：`##` + 空白 + 标题（`###` 不会命中，理由同上）。 */
const HEADING_LEVEL_2 = /^##[ \t]+(.*)$/u;

/** 类型行：`> 类型：xxx`（全角冒号，与导出格式一致；半角也容忍）。 */
const GENRE_LINE = /^>[ \t]*类型[：:][ \t]*(.*)$/u;

/** 简介行：`> 简介：xxx`。 */
const SUMMARY_LINE = /^>[ \t]*简介[：:][ \t]*(.*)$/u;

/** 导出统计段：`共 N 章，总字数 M 字。` */
const EXPORT_STATS_LINE = /^共[ \t]*\d+[ \t]*章[，,][ \t]*总字数[ \t]*\d+[ \t]*字。$/u;

/** 章标题的序号前缀：`第 N 章 `（N 为阿拉伯数字，章后可无空格）。 */
const CHAPTER_NUMBER_PREFIX = /^第[ \t]*\d+[ \t]*章[ \t　]*(.*)$/u;

/**
 * 文本字段：非字符串按空串处理。
 * @param {unknown} value
 * @returns {string}
 */
function text(value) {
  return typeof value === 'string' ? value : '';
}

/**
 * 把内容统一成 `\n` 换行的行数组。
 * @param {unknown} markdown
 * @returns {string[]}
 */
function toLines(markdown) {
  const source = text(markdown).replace(/\r\n/gu, '\n').replace(/\r/gu, '\n');
  return source.split('\n');
}

/**
 * 丢弃末尾的导出统计段：最后一行是 `共 N 章，总字数 M 字。`，且它上方最近的
 * 非空行正好是 `---` 时，把 `---` 及其后的所有行全部切掉。
 * 不满足条件（例如用户正文里恰好有 `共 N 章…`）时原样返回。
 * @param {string[]} lines
 * @returns {string[]}
 */
function stripExportStats(lines) {
  let statsIndex = -1;
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    if (EXPORT_STATS_LINE.test(lines[i].trim())) {
      statsIndex = i;
      break;
    }
  }
  if (statsIndex < 0) return lines;

  let separatorIndex = -1;
  for (let i = statsIndex - 1; i >= 0; i -= 1) {
    if (lines[i].trim() === '') continue;
    if (lines[i].trim() === '---') separatorIndex = i;
    break;
  }
  if (separatorIndex < 0) return lines;
  return lines.slice(0, separatorIndex);
}

/**
 * 读取书籍级信息：第一个一级标题（书名）与紧随其后的 `> 类型：` / `> 简介：`。
 *
 * 元信息块只扫「一级标题之后、第一个既非空行也不以 `>` 开头的行」之前的部分，
 * 与导出顺序一致。
 *
 * @param {string[]} lines
 * @returns {{ title: string, genre: string|null, summary: string|null, bodyStart: number }}
 *   bodyStart 为书籍级信息之后的第一行下标（无一级标题时为 0）
 */
function readHeader(lines) {
  let headingIndex = -1;
  let title = '';
  for (let i = 0; i < lines.length; i += 1) {
    const matched = HEADING_LEVEL_1.exec(lines[i]);
    if (matched === null) continue;
    const candidate = matched[1].trim();
    if (candidate === '') continue;
    headingIndex = i;
    title = candidate;
    break;
  }

  if (headingIndex < 0) {
    return { title: '', genre: null, summary: null, bodyStart: 0 };
  }

  let genre = null;
  let summary = null;
  let bodyStart = lines.length;
  for (let i = headingIndex + 1; i < lines.length; i += 1) {
    const line = lines[i];
    if (line.trim() === '' || line.trimStart().startsWith('>')) {
      const genreMatched = GENRE_LINE.exec(line.trim());
      if (genreMatched !== null) genre = genreMatched[1].trim();
      const summaryMatched = SUMMARY_LINE.exec(line.trim());
      if (summaryMatched !== null) summary = summaryMatched[1].trim();
      continue;
    }
    bodyStart = i;
    break;
  }

  return { title, genre, summary, bodyStart };
}

/**
 * 章标题规范化：剥掉 `第 N 章 ` 序号前缀（往返对齐导出格式），空标题兜底。
 * @param {string} raw `## ` 之后的文字
 * @returns {string}
 */
function normalizeChapterTitle(raw) {
  let title = text(raw).trim();
  const matched = CHAPTER_NUMBER_PREFIX.exec(title);
  if (matched !== null) title = matched[1].trim();
  return title === '' ? FALLBACK_CHAPTER_TITLE : title;
}

/**
 * 去掉首尾空行后拼回正文（内部空行原样保留）。
 * @param {string[]} lines
 * @returns {string}
 */
function joinBody(lines) {
  let start = 0;
  let end = lines.length;
  while (start < end && lines[start].trim() === '') start += 1;
  while (end > start && lines[end - 1].trim() === '') end -= 1;
  return lines.slice(start, end).join('\n');
}

/**
 * escapeMarkdownBody 的逆函数：去掉转义用的前导反斜杠、把 `\\` 还原成 `\`。
 *
 * 实现方式是从左到右的单遍扫描：遇到 `\` 就把它和紧随其后的字符一起吞掉，
 * 只输出后一个字符。这样 `\\` → `\`、`\#` → `#`、`\-\-\-` → `---`、
 * ` ``` ` → ` ``` `，与 escapeMarkdownBody 的「先翻倍反斜杠、再逐行加前缀」
 * 顺序互为逆操作，对任意文本都满足往返恒等。
 *
 * @param {unknown} content 转义后的正文
 * @returns {string} 还原后的正文（txt 格式不需要调用本函数）
 */
export function unescapeMarkdownBody(content) {
  const source = text(content).replace(/\r\n/gu, '\n');
  if (source === '') return '';
  let out = '';
  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i];
    if (ch === '\\' && i + 1 < source.length) {
      out += source[i + 1];
      i += 1;
      continue;
    }
    out += ch;
  }
  return out;
}

/** 三级标题行：`###` + 空白 + 标题（`####` 不会命中，理由同上）。 */
const HEADING_LEVEL_3 = /^###[ \t]+(.*)$/u;

/** 预览结果里最多带出的章标题数量。 */
const PREVIEW_TITLE_LIMIT = 3;

/**
 * 规范化拆章标题级别：只接受 2 或 3。
 *
 * 缺省（undefined / null）按默认 2 处理；其它值（1、4、字符串 `'3'` 等）一律抛
 * TypeError，避免「静默按 2 级拆章」这种看不出来的错误口径。
 *
 * @param {unknown} value
 * @returns {2 | 3}
 */
export function normalizeHeadingLevel(value) {
  if (value === undefined || value === null) return 2;
  if (value === 2 || value === 3) return value;
  throw new TypeError('headingLevel 只支持 2 或 3');
}

/**
 * 把一份 Markdown 解析成「书 + 章节」结构（纯函数，不落库）。
 *
 * headingLevel 决定按几级标题拆章（默认 2，行为与历史版本完全一致）：
 *   - 2：`## 标题` 拆章，`### ` 及以下原样留在正文里；
 *   - 3：`### 标题` 拆章，`# 书名` 仍是书名；第一个 `### ` 之前的内容（含 `## `
 *     行本身）作为首章前置内容保留，文档中部出现的 `## ` 行留在它所属章节的正文里；
 *     整篇没有 `### ` 时退回「整篇一章、章名用书名」，与 2 级口径一致。
 *
 * @param {unknown} markdown Markdown 原文
 * @param {{ filename?: unknown, headingLevel?: unknown }} [options]
 *   filename：无一级标题时用文件名（去掉 .md/.MD）作书名；
 *   headingLevel：拆章标题级别，只接受 2 或 3（缺省 2，其它值抛 TypeError）
 * @returns {{ book: { title: string, genre: string|null, summary: string|null },
 *   chapters: Array<{ title: string, content: string, wordCount: number }> }}
 */
export function parseMarkdownBook(markdown, { filename, headingLevel } = {}) {
  const level = normalizeHeadingLevel(headingLevel);
  /** 章标题行：2 级用 `## `，3 级用 `### `。 */
  const chapterHeading = level === 3 ? HEADING_LEVEL_3 : HEADING_LEVEL_2;
  const lines = stripExportStats(toLines(markdown));
  const header = readHeader(lines);

  const fallbackFromFile = text(filename).trim().replace(/\.md$/iu, '').trim();
  const bookTitle =
    header.title !== ''
      ? header.title
      : fallbackFromFile !== ''
        ? fallbackFromFile
        : FALLBACK_BOOK_TITLE;

  /** @type {Array<{ title: string, lines: string[] }>} */
  const rawChapters = [];
  /** 第一个章标题之前的内容：2 级口径下按既有约定忽略（导出格式里不会有）。 */
  const preamble = [];
  /** @type {{ title: string, lines: string[] } | null} */
  let current = null;

  for (let i = header.bodyStart; i < lines.length; i += 1) {
    const line = lines[i];
    const matched = chapterHeading.exec(line);
    if (matched !== null) {
      if (current !== null) rawChapters.push(current);
      current = { title: normalizeChapterTitle(matched[1]), lines: [] };
      continue;
    }
    if (current === null) {
      preamble.push(line);
      continue;
    }
    current.lines.push(line);
  }
  if (current !== null) rawChapters.push(current);

  // 3 级口径下，首个 `### ` 之前的内容（含 `## ` 行本身）要并进首章正文，不能丢。
  const preambleText = level === 3 ? joinBody(preamble) : '';

  /** @type {Array<{ title: string, content: string, wordCount: number }>} */
  const chapters = [];

  if (rawChapters.length === 0) {
    // 整篇没有章标题（2 级没有 `## `；3 级没有 `### `）：正文非空时只有一章
    // （章标题用书名），否则视为空结构（0 章）。
    const body = joinBody(lines.slice(header.bodyStart));
    if (body.trim() !== '') {
      const content = unescapeMarkdownBody(body);
      chapters.push({ title: bookTitle, content, wordCount: countWords(content) });
    }
  } else {
    rawChapters.forEach((item, index) => {
      const body = joinBody(item.lines);
      // 首章把前置内容接在最前面（用单个空行分隔，避免空行堆积）。
      const merged =
        index === 0 && preambleText !== ''
          ? body === ''
            ? preambleText
            : `${preambleText}\n\n${body}`
          : body;
      const content = unescapeMarkdownBody(merged);
      chapters.push({ title: item.title, content, wordCount: countWords(content) });
    });
  }

  return {
    book: { title: bookTitle, genre: header.genre, summary: header.summary },
    chapters,
  };
}

/**
 * 导入预览的纯函数（不落库、不读 DB、无文件 IO）：只从解析结果里取书籍信息与
 * 前几章标题。解析规则完全复用 parseMarkdownBook，本函数不重复实现任何解析逻辑。
 *
 * @param {unknown} markdown Markdown 原文
 * @param {{ filename?: unknown, headingLevel?: unknown }} [options]
 *   与 parseMarkdownBook 完全一致的选项（headingLevel 只接受 2 或 3）
 * @returns {{ book: { title: string, genre: string|null, summary: string|null },
 *   chapterCount: number, chapterTitles: string[] }} chapterTitles 最多前 3 章标题
 */
export function previewMarkdownImport(markdown, { filename, headingLevel } = {}) {
  const parsed = parseMarkdownBook(markdown, { filename, headingLevel });
  return {
    book: {
      title: parsed.book.title,
      genre: parsed.book.genre,
      summary: parsed.book.summary,
    },
    chapterCount: parsed.chapters.length,
    chapterTitles: parsed.chapters.slice(0, PREVIEW_TITLE_LIMIT).map((chapter) => chapter.title),
  };
}
