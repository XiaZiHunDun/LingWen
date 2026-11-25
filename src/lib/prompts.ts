// 提示词构造函数（纯函数：不读环境变量、不访问网络、不修改入参、无随机与时间依赖）。
// 约定：每个 build* 返回 { system, user }，配合 toMessages() 可直接喂给 llm.ts 的 chat / chatStream。

import type { ChatMessage } from './llm';
import type { Character, OutlineItem, WorldEntry } from './types';

/** 作品信息允许只提供部分字段，缺省视为未填写、不注入提示词。 */
export interface PromptProject {
  title?: string;
  genre?: string;
  style?: string;
  synopsis?: string;
  targetWords?: number;
}

/** 近期章节（续写时作为前情提要保持连贯）。 */
export interface PromptChapter {
  title?: string;
  content: string;
}

/** 一次生成可复用的上下文；各字段均为可选。 */
export interface PromptContext {
  project?: PromptProject;
  characters?: Array<Pick<Character, 'name' | 'role' | 'traits' | 'description'>>;
  entries?: Array<Pick<WorldEntry, 'category' | 'name' | 'content'>>;
  outline?: OutlineItem[];
  recentChapters?: PromptChapter[];
}

export interface PromptMessages {
  system: string;
  user: string;
}

export interface ContinuePromptOptions {
  context?: PromptContext;
  chapterTitle?: string;
  /** 本章已有正文，通常传尾部若干段。 */
  priorText?: string;
  instruction?: string;
  /** 本次期望的续写字数。 */
  targetWords?: number;
}

export interface RewritePromptOptions {
  text: string;
  context?: PromptContext;
  instruction?: string;
}

export interface ExpandPromptOptions extends RewritePromptOptions {
  /** 目标总字数；与 ratio 二选一，targetWords 优先。 */
  targetWords?: number;
  /** 目标倍数（相对原文字数），默认 1.8。 */
  ratio?: number;
}

export interface OutlinePromptOptions {
  context?: PromptContext;
  /** 期望的大纲条目数，默认 12。 */
  chapterCount?: number;
  instruction?: string;
}

// —— 截断上限（字符数），避免提示词无限膨胀 ——
export const MAX_SYNOPSIS = 800;
export const MAX_PRIOR_TEXT = 4000;
export const MAX_CHAPTER_TEXT = 1200;
const MAX_CHARACTER = 160;
const MAX_ENTRY = 200;
const MAX_OUTLINE_ITEMS = 30;
const MAX_RECENT_CHAPTERS = 3;

const DEFAULT_SYSTEM =
  '你是一位资深中文小说作者，熟悉长篇连载的节奏控制与人物塑造。你的写作必须服从既定设定、大纲与文风，不得擅自改动已有事实。';

const PLAIN_OUTPUT = '只输出正文，不要写标题、不要解释思路、不要使用 Markdown 标记或代码块。';

/** 去空白并截断，超长以省略号收尾。 */
function clip(text: unknown, limit: number): string {
  const value = typeof text === 'string' ? text.trim() : '';
  if (value.length <= limit) return value;
  return `${value.slice(0, limit)}…`;
}

/** 丢弃空段落，用一个空行拼接。 */
function joinSections(sections: Array<string | null | undefined>): string {
  return sections.filter((s): s is string => typeof s === 'string' && s.trim() !== '').join('\n\n');
}

function positiveInt(value: unknown, fallback: number): number {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) && n > 0 ? Math.round(n) : fallback;
}

/** 作品基本信息块。 */
export function describeProject(project?: PromptProject): string {
  if (!project) return '';
  const title = clip(project.title, 60);
  const genre = clip(project.genre, 40);
  const style = clip(project.style, 60);
  const head = [
    title ? `《${title}》` : '',
    genre ? `类型：${genre}` : '',
    style ? `文风：${style}` : '',
  ]
    .filter(Boolean)
    .join(' ｜ ');
  const synopsis = clip(project.synopsis, MAX_SYNOPSIS);
  return joinSections([
    head ? `【作品】${head}` : '',
    synopsis ? `【故事梗概】${synopsis}` : '',
  ]);
}

/** 人物设定块。 */
export function describeCharacters(
  characters?: PromptContext['characters'],
): string {
  const list = Array.isArray(characters) ? characters : [];
  const lines = list
    .map((c) => {
      const name = clip(c.name, 30);
      if (!name) return '';
      const role = clip(c.role, 30);
      const traits = clip(c.traits, MAX_CHARACTER);
      const description = clip(c.description, MAX_CHARACTER);
      const detail = [traits, description].filter(Boolean).join('；');
      return `- ${name}${role ? `（${role}）` : ''}${detail ? `：${detail}` : ''}`;
    })
    .filter(Boolean);
  return lines.length > 0 ? `【主要人物】\n${lines.join('\n')}` : '';
}

/** 世界观设定块。 */
export function describeWorld(entries?: PromptContext['entries']): string {
  const list = Array.isArray(entries) ? entries : [];
  const lines = list
    .map((e) => {
      const name = clip(e.name, 40);
      if (!name) return '';
      const category = clip(e.category, 20);
      const content = clip(e.content, MAX_ENTRY);
      return `- ${category ? `[${category}] ` : ''}${name}${content ? `：${content}` : ''}`;
    })
    .filter(Boolean);
  return lines.length > 0 ? `【世界观设定】\n${lines.join('\n')}` : '';
}

/** 既定大纲块（最多 MAX_OUTLINE_ITEMS 条）。 */
export function describeOutline(outline?: OutlineItem[]): string {
  const list = Array.isArray(outline) ? outline.slice(0, MAX_OUTLINE_ITEMS) : [];
  const lines = list
    .map((item, index) => {
      const title = clip(item?.title, 60);
      if (!title) return '';
      const summary = clip(item?.summary, MAX_ENTRY);
      return `${index + 1}. ${title}${summary ? ` —— ${summary}` : ''}`;
    })
    .filter(Boolean);
  return lines.length > 0 ? `【既定大纲】\n${lines.join('\n')}` : '';
}

/** 近期章节块（取最后 MAX_RECENT_CHAPTERS 章，每章截断）。 */
export function describeRecentChapters(chapters?: PromptChapter[]): string {
  const list = Array.isArray(chapters) ? chapters.slice(-MAX_RECENT_CHAPTERS) : [];
  const lines = list
    .map((chapter) => {
      const title = clip(chapter?.title, 60);
      const content = clip(chapter?.content, MAX_CHAPTER_TEXT);
      if (!content) return '';
      return `- ${title || '未命名章节'}：${content}`;
    })
    .filter(Boolean);
  return lines.length > 0 ? `【近期章节】\n${lines.join('\n')}` : '';
}

/** 把上下文渲染为提示词里的一段，永远返回字符串（可能为空）。 */
export function buildContextBlock(context?: PromptContext): string {
  if (!context) return '';
  return joinSections([
    describeProject(context.project),
    describeCharacters(context.characters),
    describeWorld(context.entries),
    describeOutline(context.outline),
    describeRecentChapters(context.recentChapters),
  ]);
}

/** 一、续写：承接已有正文往下写。 */
export function buildContinuePrompt(options: ContinuePromptOptions = {}): PromptMessages {
  const { context, chapterTitle, priorText, instruction } = options;
  const words = positiveInt(options.targetWords, 800);
  const title = clip(chapterTitle, 60);
  const prior = clip(priorText, MAX_PRIOR_TEXT);

  const user = joinSections([
    buildContextBlock(context),
    title ? `【当前章节】${title}` : '',
    prior ? `【已有正文（结尾部分）】\n${prior}` : '【已有正文】本章尚未开始，请直接写出开头。',
    `【写作要求】${clip(instruction, 400) || '承接前文情节自然推进，保持人物口吻、叙事视角与段落节奏一致。'}`,
    `【篇幅】约 ${words} 字。`,
  ]);

  return {
    system: `${DEFAULT_SYSTEM}${PLAIN_OUTPUT}`,
    user,
  };
}

/** 二、润色：不改情节，只改表达。 */
export function buildPolishPrompt(options: RewritePromptOptions): PromptMessages {
  const { text, context, instruction } = options;
  const source = typeof text === 'string' ? text.trim() : '';

  const user = joinSections([
    buildContextBlock(context),
    `【待润色正文】\n${source}`,
    `【润色要求】${
      clip(instruction, 400) ||
      '在不改变情节、人物设定与叙事视角的前提下，提升语言的准确、流畅与画面感，统一文风，修正错别字与标点；篇幅与原文相当。'
    }`,
    '【输出】只输出润色后的完整正文，不要附加修改说明。',
  ]);

  return {
    system: `你是一位严谨的中文文字编辑，擅长在不损失作者风格的前提下打磨文本。${PLAIN_OUTPUT}`,
    user,
  };
}

/** 三、扩写：补细节、不跑偏。 */
export function buildExpandPrompt(options: ExpandPromptOptions): PromptMessages {
  const { text, context, instruction } = options;
  const source = typeof text === 'string' ? text.trim() : '';
  const ratio = positiveInt(Math.round((Number(options.ratio) || 1.8) * 10), 18) / 10;
  const target =
    options.targetWords !== undefined
      ? `约 ${positiveInt(options.targetWords, Math.max(1, Math.round(source.length * ratio)))} 字`
      : `约为原文的 ${ratio} 倍`;

  const user = joinSections([
    buildContextBlock(context),
    `【待扩写正文】\n${source}`,
    `【扩写要求】${
      clip(instruction, 400) ||
      '在不新增无关情节与人物、不改变原有事件顺序的前提下，补充动作、环境与心理细节，使场景更饱满、节奏更从容。'
    }`,
    `【篇幅】${target}。`,
    '【输出】只输出扩写后的完整正文。',
  ]);

  return {
    system: `${DEFAULT_SYSTEM}你的扩写必须服务于已有文本，不能另起炉灶。${PLAIN_OUTPUT}`,
    user,
  };
}

/** 四、大纲：产出可直接被 outline.js 解析的 Markdown 条目。 */
export function buildOutlinePrompt(options: OutlinePromptOptions = {}): PromptMessages {
  const { context, instruction } = options;
  const count = positiveInt(options.chapterCount, 12);
  const project = context?.project;
  const targetWords = positiveInt(project?.targetWords, 0);

  const user = joinSections([
    buildContextBlock(context),
    `【任务】规划全书共 ${count} 章的章节大纲。`,
    targetWords > 0 ? `【全书目标字数】约 ${targetWords} 字。` : '',
    `【额外要求】${clip(instruction, 400) || '每章推进明确冲突，章与章之间留有钩子；避免流水账与重复桥段。'}`,
    `【输出格式】每行一条，恰好 ${count} 行，格式为 \`1. 章节标题 —— 一句话摘要\`；不要输出标题、序号说明或其他内容。`,
  ]);

  return {
    system:
      '你是一位长篇小说策划编辑，擅长搭建结构清晰、张弛有度的章节大纲。输出必须严格遵守给定格式，便于程序解析。',
    user,
  };
}

/** 转成 llm.ts 的 ChatMessage[]，顺序固定为 system → user。 */
export function toMessages(prompt: PromptMessages): ChatMessage[] {
  return [
    { role: 'system', content: prompt.system },
    { role: 'user', content: prompt.user },
  ];
}
