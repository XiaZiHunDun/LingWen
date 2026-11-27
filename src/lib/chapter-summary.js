/**
 * 章节摘要（纯函数）：归一化摘要文本 + 组装摘要生成 prompt。
 *
 * 设计约束：
 *   1. 纯函数：不读环境变量、不访问网络 / 数据库、不修改入参、无随机与时间依赖；
 *   2. summary 路由用本模块拼 prompt、压长度，保证落库的摘要稳定在 ≤200 字；
 *   3. 摘要用于「下一章的前情提要」，因此要求单段、不分点、不复述原文。
 */

/** 摘要最大字符数（与 chapter-context 的 SUMMARY_CHARS 对齐）。 */
export const SUMMARY_MAX_CHARS = 200;
/** 摘要请求用的 maxTokens（200 中文字符足够）。 */
export const SUMMARY_MAX_TOKENS = 400;
/** 拼 prompt 时正文最多带多少字，超出则截断并标注。 */
export const SUMMARY_PROMPT_CONTENT_CHARS = 6000;

/** 截断标记。 */
const ELLIPSIS = '…';

/** 正整数字段归一。 */
function toPositiveInt(value, fallback) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback;
  const rounded = Math.floor(value);
  return rounded > 0 ? rounded : fallback;
}

/** 需要剥掉的包裹引号（成对）。 */
const QUOTE_PAIRS = [
  ['「', '」'],
  ['『', '』'],
  ['“', '”'],
  ['"', '"'],
  ["'", "'"],
];

/**
 * 归一化摘要文本：
 *   - 去 Markdown 记号（代码围栏、标题、列表、强调、行内代码、链接、引用符）；
 *   - 去包裹引号；
 *   - 空白压成单空格（压成单段）；
 *   - 超长截断到 ≤ limit 字符，以「…」收尾。
 *
 * @param {unknown} text LLM 返回的原始文本
 * @param {number} [limit]
 * @returns {string}
 */
export function clipSummary(text, limit = SUMMARY_MAX_CHARS) {
  const max = toPositiveInt(limit, SUMMARY_MAX_CHARS);
  let raw = typeof text === 'string' ? text : '';

  raw = raw.replace(/```[^\n]*\n?/g, ' ').replace(/```/g, ' ');
  raw = raw.replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1');
  raw = raw.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1');
  raw = raw.replace(/^[ \t]{0,3}#{1,6}[ \t]*/gm, ' ');
  raw = raw.replace(/^[ \t]{0,3}>[ \t]?/gm, ' ');
  raw = raw.replace(/^[ \t]{0,3}(?:[-*+•]|\d+[.、)]|[（(]\d+[)）])[ \t]+/gm, ' ');
  raw = raw.replace(/[*_~`]+/g, '');
  raw = raw.replace(/\s+/g, ' ').trim();

  let changed = true;
  while (changed) {
    changed = false;
    for (const [open, close] of QUOTE_PAIRS) {
      if (raw.length > open.length + close.length && raw.startsWith(open) && raw.endsWith(close)) {
        raw = raw.slice(open.length, raw.length - close.length).trim();
        changed = true;
      }
    }
  }

  if (raw.length <= max) return raw;
  return `${raw.slice(0, Math.max(1, max - ELLIPSIS.length))}${ELLIPSIS}`;
}

/**
 * 组装章节摘要的 system / user prompt。
 *
 * @param {{ title?: unknown, content?: unknown, maxChars?: number }} [params]
 * @returns {{ system: string, user: string }}
 */
export function buildChapterSummaryPrompt({ title, content, maxChars } = {}) {
  const max = toPositiveInt(maxChars, SUMMARY_MAX_CHARS);
  const rawTitle = typeof title === 'string' ? title.trim() : '';
  const chapterTitle = rawTitle === '' ? '（未命名章节）' : rawTitle;
  const body = typeof content === 'string' ? content.trim() : '';
  const contentLimit = SUMMARY_PROMPT_CONTENT_CHARS;
  const truncated = body.length > contentLimit;
  const excerpt = truncated
    ? `${body.slice(0, contentLimit)}\n（正文已截断，以上为前 ${contentLimit} 字）`
    : body;

  const system = [
    '你是中文小说编辑，负责为章节撰写剧情摘要。',
    '硬性要求：',
    `1. 只输出一段简体中文摘要，不超过 ${max} 字。`,
    '2. 不分点、不加小标题、不写「摘要：」之类的前缀，不使用 Markdown。',
    '3. 不要复述原文句子，用简洁的叙述概括本章发生了什么。',
    '4. 保留关键人物、地点与情节推进，方便后续章节衔接。',
  ].join('\n');

  const user = [
    `【章节标题】${chapterTitle}`,
    `【章节正文】\n${excerpt === '' ? '（正文为空）' : excerpt}`,
    `请用不超过 ${max} 字的中文摘要概括本章内容，只输出摘要文本。`,
  ].join('\n\n');

  return { system, user };
}
