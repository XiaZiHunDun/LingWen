// 润色提示词构造（纯函数：不读环境变量、不访问网络、不修改入参、无随机与时间依赖）。
// 两种模式：整章润色（selection 为空）与选中片段改写（selection 非空）。

/** 选中片段最大长度（字符）；超过直接拒绝。 */
export const MAX_SELECTION_CHARS = 4000;
/** 选区前后上下文各自注入提示词的最大长度（字符）。 */
export const MAX_CONTEXT_CHARS = 500;
/** 书籍设定注入 prompt 的最大长度（字符）。 */
export const MAX_BOOK_SETTINGS = 2000;
/** 本章大纲注入 prompt 的最大长度（字符）。 */
export const MAX_OUTLINE_SUMMARY = 600;
/** 额外要求注入 prompt 的最大长度（字符）。 */
export const MAX_INSTRUCTION = 800;
/** 输出 token 上限。 */
const MAX_OUTPUT_TOKENS = 8000;

/** 选中内容校验失败（路由据此回 400）。 */
export class PolishSelectionError extends Error {
  constructor(message) {
    super(message);
    this.name = 'PolishSelectionError';
    this.status = 400;
  }
}

function toText(value) {
  return typeof value === 'string' ? value : '';
}

/** 截断并加省略号（用于设定 / 大纲等注入块）。 */
function clip(text, limit) {
  const trimmed = toText(text).trim();
  return trimmed.length > limit ? `${trimmed.slice(0, limit)}…` : trimmed;
}

/** 选区上下文截断：纯截断、不加省略号，保证长度不超过上限。 */
export function clipSelectionContext(text) {
  const value = toText(text).trim();
  return value.length > MAX_CONTEXT_CHARS ? value.slice(0, MAX_CONTEXT_CHARS) : value;
}

/**
 * 归一化选中片段参数。
 * - selection trim 后为空 → fragment=false（整章模式）
 * - selection 超长 → 抛 PolishSelectionError（message 即 400 文案）
 * - before / after 各截断到 MAX_CONTEXT_CHARS
 */
export function normalizePolishSelection(input) {
  const source = input ?? {};
  const selection = toText(source.selection).trim();
  if (selection.length > MAX_SELECTION_CHARS) {
    throw new PolishSelectionError(`选中内容过长（最多 ${MAX_SELECTION_CHARS} 字），请缩小范围`);
  }
  return {
    fragment: selection !== '',
    selection,
    before: clipSelectionContext(source.before),
    after: clipSelectionContext(source.after),
  };
}

/** mode 归一：非法值退回 polish。 */
export function parsePolishMode(value) {
  if (value === 'condense' || value === 'expand' || value === 'polish') return value;
  return 'polish';
}

/** 每种模式对应的任务描述（整章模式）。 */
function taskLine(mode) {
  switch (mode) {
    case 'condense':
      return '【任务】在保留全部关键情节、人物动作与对话功能的前提下，精简本章正文，删掉冗余表达与重复铺陈，使篇幅明显缩短、节奏更紧凑。';
    case 'expand':
      return '【任务】在保持原有情节走向、人物与设定不变的前提下，扩写本章正文，补充细节描写、心理活动、环境与动作描写，使内容更饱满。';
    default:
      return '【任务】润色本章正文：优化措辞、句式与节奏，修正错别字与病句，统一叙事人称与语气，情节、人物、设定一律不得改动。';
  }
}

/** 每种模式对应的任务描述（片段模式：只作用在选中片段上）。 */
function fragmentTaskLine(mode) {
  switch (mode) {
    case 'condense':
      return '在保留选中片段全部关键信息与人物动作的前提下精简其表达，篇幅明显缩短。';
    case 'expand':
      return '在不改变情节走向的前提下扩写选中片段，补充细节描写、心理活动、环境与动作描写。';
    default:
      return '润色选中片段：优化措辞、句式与节奏，修正错别字与病句。';
  }
}

/** 由正文长度估算输出 token 上限：扩写需要更大余量。 */
export function estimatePolishMaxTokens(mode, contentLength) {
  const length = Number.isFinite(contentLength) && contentLength > 0 ? contentLength : 0;
  const factor = mode === 'expand' ? 2 : mode === 'condense' ? 1 : 1.4;
  return Math.max(1500, Math.min(MAX_OUTPUT_TOKENS, Math.round(length * factor) + 500));
}

const WHOLE_SYSTEM = [
  '你是一位资深中文小说编辑，负责在保持原意的前提下修改章节正文。',
  '硬性要求：',
  '1. 只输出修改后的完整正文，一次输出全文，不要分段截断。',
  '2. 不要输出任何解释、说明、点评、建议或改动清单。',
  '3. 不要使用 Markdown：不要 ``` 代码块围栏、不要 #、不要列表符号、不要加粗。',
  '4. 不要输出章节标题行或章节号，直接输出正文。',
  '5. 不要输出「以下是修改后的正文」这类前言或收尾语。',
  '6. 使用简体中文，段落之间空一行。',
].join('\n');

const FRAGMENT_SYSTEM = [
  '你是一位资深中文小说编辑，本次只改写用户选中的一小段文字。',
  '硬性要求：',
  '1. 只输出改写后的片段本身，不要带任何前后文、标题或说明。',
  '2. 不要输出解释、点评、建议或改动清单。',
  '3. 不要使用 Markdown：不要 ``` 代码块围栏、不要 #、不要列表符号、不要加粗。',
  '4. 不要输出「以下是修改后的片段」这类前言或收尾语。',
  '5. 使用简体中文。',
].join('\n');

/**
 * 构造润色提示词。
 *
 * @param {object} [options]
 * @param {'polish'|'condense'|'expand'} [options.mode]
 * @param {string} [options.chapterTitle] 本章标题
 * @param {string} [options.bookSettings] 已渲染好的书籍设定块（服务端已截断）
 * @param {string} [options.outline] 已渲染好的本章大纲块
 * @param {string} [options.content] 整章正文（整章模式使用）
 * @param {string} [options.instruction] 额外要求
 * @param {string} [options.selection] 选中片段（非空即片段模式）
 * @param {string} [options.before] 选区前文（前端截好，服务端再截 500）
 * @param {string} [options.after] 选区后文（前端截好，服务端再截 500）
 * @returns {{ fragment: boolean, system: string, user: string, maxTokens: number }}
 */
export function buildPolishPrompt(options = {}) {
  const mode = parsePolishMode(options.mode);
  const title = clip(options.chapterTitle, 60);
  const bookSettings = clip(options.bookSettings, MAX_BOOK_SETTINGS);
  const outline = clip(options.outline, MAX_OUTLINE_SUMMARY);
  const instruction = clip(options.instruction, MAX_INSTRUCTION);
  const { fragment, selection, before, after } = normalizePolishSelection({
    selection: options.selection,
    before: options.before,
    after: options.after,
  });

  const head = [];
  if (bookSettings !== '') head.push(`【书籍设定】\n${bookSettings}`);
  if (outline !== '') head.push(`【本章大纲】\n${outline}`);
  head.push(`【本章标题】${title}`);

  if (fragment) {
    const lines = [...head];
    if (before !== '') lines.push(`【上文】\n${before}`);
    lines.push(`【选中片段】\n${selection}`);
    if (after !== '') lines.push(`【下文】\n${after}`);
    lines.push(`【任务】${fragmentTaskLine(mode)}`);
    lines.push(
      [
        '【改写要求】',
        '1. 保持叙事人称、语气与文风不变。',
        '2. 与前后文自然衔接，不要重复上下文中已有的句子。',
        '3. 不新增未出现的人物、设定或情节。',
        '4. 情节走向与事件顺序不变。',
      ].join('\n'),
    );
    if (instruction !== '') lines.push(`【额外要求】${instruction}`);
    lines.push('只输出改写后的【选中片段】本身：不要复述上下文，不要输出解释，不要带任何前后文。');

    return {
      fragment: true,
      system: FRAGMENT_SYSTEM,
      user: lines.join('\n\n'),
      maxTokens: estimatePolishMaxTokens(mode, selection.length),
    };
  }

  const content = toText(options.content);
  const lines = [...head];
  lines.push(`【原文正文】\n${content}`);
  lines.push(taskLine(mode));
  if (instruction !== '') lines.push(`【额外要求】${instruction}`);
  lines.push('请直接输出修改后的完整正文。');

  return {
    fragment: false,
    system: WHOLE_SYSTEM,
    user: lines.join('\n\n'),
    maxTokens: estimatePolishMaxTokens(mode, content.length),
  };
}
