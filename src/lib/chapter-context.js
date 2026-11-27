/**
 * 章节续写上下文组装（纯函数）。
 *
 * 目标：让「AI 记得前文」——把上一章正文结尾、更早章节摘要、设定集、本章大纲、
 * 已有正文衔接段、目标字数与任务要求拼成稳定的用户提示词（userPrompt）。
 *
 * 设计约束：
 *   1. 纯函数：不读环境变量、不访问网络 / 数据库、不修改入参、无随机与时间依赖；
 *   2. generate 路由与只读预览接口共用本模块，保证「预览 = 实际注入」；
 *   3. 所有截断都带「…」标记，且截断后总长度不超过给定上限。
 */

/** 上一章正文结尾注入 prompt 的最大字符数。 */
export const PREV_TAIL_CHARS = 2000;
/** 更早章节摘要每章最大字符数。 */
export const SUMMARY_CHARS = 200;
/** 更早章节没有摘要时，取正文开头的最大字符数。 */
export const FALLBACK_OPENING_CHARS = 200;
/** 更早章节最多注入多少章（保留最近的若干章）。 */
export const MAX_EARLIER_CHAPTERS = 20;
/** 设定集最多注入多少条。 */
export const MAX_BIBLE_ITEMS = 20;
/** 单条设定集内容最大字符数。 */
export const BIBLE_SNIPPET_CHARS = 300;
/** 本章大纲摘要最大字符数。 */
export const OUTLINE_SUMMARY_CHARS = 300;
/** 本章已有正文回灌 prompt 时只取末尾多少字符。 */
export const EXISTING_TAIL_CHARS = 600;
/** 额外要求最大字符数。 */
export const INSTRUCTION_CHARS = 800;

/** 截断标记。 */
const ELLIPSIS = '…';

/** 字符串归一：非字符串一律空串，避免 prompt 里出现 [object Object]。 */
function toText(value) {
  return typeof value === 'string' ? value : '';
}

/** 数值归一：非有限数一律 null。 */
function toNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

/** 正整数字段归一：非法值回退到 fallback。 */
function toPositiveInt(value, fallback) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback;
  const rounded = Math.floor(value);
  return rounded > 0 ? rounded : fallback;
}

/** 内部：按上限截断，超长时保留 limit-1 个字符 + 「…」，结果长度恰好 ≤ limit。 */
function truncate(text, limit, fromEnd) {
  const raw = toText(text);
  const max = toPositiveInt(limit, 1);
  if (raw.length <= max) return raw;
  const keep = Math.max(1, max - ELLIPSIS.length);
  const piece = fromEnd ? raw.slice(raw.length - keep) : raw.slice(0, keep);
  return `${piece}${ELLIPSIS}`;
}

/**
 * 取文本开头，超长时以「…」收尾。
 * @param {unknown} text
 * @param {number} [limit]
 * @returns {string}
 */
export function clipText(text, limit = BIBLE_SNIPPET_CHARS) {
  return truncate(text, limit, false);
}

/**
 * 取文本开头（等价于 clipText，语义更明确：用于「正文开头」）。
 * @param {unknown} text
 * @param {number} [limit]
 * @returns {string}
 */
export function takeHead(text, limit = FALLBACK_OPENING_CHARS) {
  return truncate(text, limit, false);
}

/**
 * 取文本结尾，超长时保留尾部并以「…」收尾。
 * @param {unknown} text
 * @param {number} [limit]
 * @returns {string}
 */
export function takeTail(text, limit = PREV_TAIL_CHARS) {
  return truncate(text, limit, true);
}

/** 章节排序键：seq 升序、其次 id 升序；缺失值排最后。 */
function seqOf(chapter) {
  const value = toNumber(chapter?.seq);
  return value === null ? Number.MAX_SAFE_INTEGER : value;
}

function idOf(chapter) {
  const value = toNumber(chapter?.id);
  return value === null ? Number.MAX_SAFE_INTEGER : value;
}

/** 章节展示名：第 N 章 标题。 */
function chapterLabel(chapter) {
  const seq = toNumber(chapter?.seq);
  const title = toText(chapter?.title).trim();
  if (seq !== null && title !== '') return `第 ${seq} 章 ${title}`;
  if (seq !== null) return `第 ${seq} 章`;
  if (title !== '') return title;
  const id = toNumber(chapter?.id);
  return id === null ? '未命名章节' : `章节 ${id}`;
}

/** 章节编号（用于 stats）。 */
function chapterNo(chapter) {
  const seq = toNumber(chapter?.seq);
  return seq === null ? idOf(chapter) : seq;
}

/**
 * 挑出当前章节之前的章节（保持 seq / id 升序）。
 * 优先按 id 在当前列表里定位；定位不到时退化为按 seq / id 比较。
 */
function chaptersBefore(sorted, current) {
  if (current === null) return [];
  const currentId = toNumber(current?.id);
  if (currentId !== null) {
    const index = sorted.findIndex((chapter) => toNumber(chapter?.id) === currentId);
    if (index >= 0) return sorted.slice(0, index);
  }
  const currentSeq = toNumber(current?.seq);
  const fallbackId = currentId === null ? Number.MAX_SAFE_INTEGER : currentId;
  return sorted.filter((chapter) => {
    const seq = toNumber(chapter?.seq);
    const id = idOf(chapter);
    if (currentSeq !== null && seq !== null && seq !== currentSeq) return seq < currentSeq;
    return id < fallbackId;
  });
}

/** limits 归一：调用方可覆盖任意上限，非法值回落默认常量。 */
function resolveLimits(raw) {
  const source = raw !== null && typeof raw === 'object' ? raw : {};
  return {
    prevTailChars: toPositiveInt(source.prevTailChars, PREV_TAIL_CHARS),
    summaryChars: toPositiveInt(source.summaryChars, SUMMARY_CHARS),
    fallbackOpeningChars: toPositiveInt(source.fallbackOpeningChars, FALLBACK_OPENING_CHARS),
    maxEarlierChapters: toPositiveInt(source.maxEarlierChapters, MAX_EARLIER_CHAPTERS),
    maxBibleItems: toPositiveInt(source.maxBibleItems, MAX_BIBLE_ITEMS),
    bibleSnippetChars: toPositiveInt(source.bibleSnippetChars, BIBLE_SNIPPET_CHARS),
    outlineSummaryChars: toPositiveInt(source.outlineSummaryChars, OUTLINE_SUMMARY_CHARS),
    existingTailChars: toPositiveInt(source.existingTailChars, EXISTING_TAIL_CHARS),
    instructionChars: toPositiveInt(source.instructionChars, INSTRUCTION_CHARS),
  };
}

/** 组装一个 block：正文为空则不产出（返回 null）。 */
function makeBlock(key, label, body) {
  const text = toText(body).trim();
  if (text === '') return null;
  const content = `【${label}】\n${text}`;
  return { key, label, content, chars: content.length };
}

/** 书籍信息块。 */
function buildBookBlock(book, limits) {
  if (book === null || typeof book !== 'object') return null;
  const lines = [];
  const title = toText(book.title).trim();
  const genre = toText(book.genre).trim();
  const style = toText(book.style).trim();
  const summary = toText(book.summary).trim();
  if (title !== '') lines.push(`书名：${title}`);
  if (genre !== '') lines.push(`类型：${genre}`);
  if (style !== '') lines.push(`风格：${style}`);
  if (summary !== '') lines.push(`全书简介：${clipText(summary, limits.bibleSnippetChars)}`);
  if (lines.length === 0) return null;
  return makeBlock('book', '书籍信息', lines.join('\n'));
}

/** 设定集 / 人物块：最多 MAX_BIBLE_ITEMS 条，每条内容截 300 字。 */
function buildBibleBlock(bible, limits) {
  const items = bible.slice(0, limits.maxBibleItems);
  const lines = [];
  for (const item of items) {
    const category = toText(item?.category).trim();
    const title = toText(item?.title).trim();
    const content = toText(item?.content).trim();
    const head = [category, title].filter((part) => part !== '').join('·');
    if (head === '' && content === '') continue;
    const snippet = clipText(content, limits.bibleSnippetChars);
    lines.push(`- ${head === '' ? '设定' : head}：${snippet === '' ? '（暂无内容）' : snippet}`);
  }
  if (lines.length === 0) return null;
  return makeBlock('bible', '设定集/人物', lines.join('\n'));
}

/**
 * 前情提要块：
 *   ① 上一章正文结尾（takeTail，默认 2000 字），标注「第 N 章 标题 · 正文结尾」；
 *   ② 更早章节摘要（每章 ≤200 字），无摘要时取正文开头 200 字并标注「（无摘要，取正文开头）」。
 */
function buildPreviousBlock(previousChapter, earlier, limits, stats) {
  if (previousChapter === null && earlier.length === 0) return null;
  const lines = [];
  if (previousChapter !== null) {
    const tail = takeTail(toText(previousChapter.content), limits.prevTailChars);
    const label = chapterLabel(previousChapter);
    if (tail !== '') {
      stats.hasPreviousTail = true;
      lines.push(`- ${label} · 正文结尾（最后 ${limits.prevTailChars} 字）：\n${tail}`);
    } else {
      lines.push(`- ${label} · 正文结尾：（上一章正文为空）`);
    }
  }
  if (earlier.length > 0) {
    lines.push(`- 更早章节（共 ${earlier.length} 章）：`);
    for (const chapter of earlier) {
      const summary = clipText(toText(chapter?.summary).trim(), limits.summaryChars);
      if (summary !== '') {
        lines.push(`  · ${chapterLabel(chapter)}：${summary}`);
      } else {
        stats.chaptersWithoutSummary.push(chapterNo(chapter));
        const head = takeHead(toText(chapter?.content), limits.fallbackOpeningChars);
        lines.push(
          `  · ${chapterLabel(chapter)}（无摘要，取正文开头）：${head === '' ? '（正文为空）' : head}`,
        );
      }
    }
  }
  return makeBlock('previous', '前情提要', lines.join('\n'));
}

/** 本章大纲块：按 currentChapter.outlineId 在 outlines 里匹配。 */
function buildOutlineBlock(outlines, current, limits) {
  const outlineId = toNumber(current?.outlineId);
  if (outlineId === null) return null;
  const matched = outlines.find((item) => toNumber(item?.id) === outlineId);
  if (matched === undefined || matched === null) return null;
  const lines = [];
  const title = toText(matched.title).trim();
  const summary = clipText(toText(matched.summary).trim(), limits.outlineSummaryChars);
  if (title !== '') lines.push(`标题：${title}`);
  if (summary !== '') lines.push(`摘要：${summary}`);
  if (lines.length === 0) return null;
  lines.push('要求：本章情节须围绕上面的大纲展开，不要偏移主线。');
  return makeBlock('outline', '本章大纲', lines.join('\n'));
}

/** 任务块文案：append / replace 两种。 */
function taskText(mode) {
  return mode === 'replace'
    ? '【任务】重写本章正文：在保留已有设定与前文脉络的前提下，输出全新的完整章节正文。'
    : '【任务】承接已有正文继续往下写，不要重复已有的句子，直接从新的内容写起。';
}

/**
 * 选择并组装本章写作上下文。
 *
 * @param {{
 *   book?: object | null,
 *   bible?: object[],
 *   outlines?: object[],
 *   chapters?: object[],
 *   currentChapter?: object | null,
 *   existingContent?: string,
 *   targetWords?: number,
 *   mode?: 'append' | 'replace',
 *   instruction?: string,
 *   limits?: object,
 * }} [input]
 * @returns {{
 *   blocks: Array<{ key: string, label: string, content: string, chars: number }>,
 *   promptText: string,
 *   totalChars: number,
 *   stats: { hasPreviousTail: boolean, previousChapterTitle: string | null, earlierCount: number, chaptersWithoutSummary: number[] },
 * }}
 */
export function selectChapterContext(input = {}) {
  const source = input !== null && typeof input === 'object' ? input : {};
  const book = source.book === undefined ? null : source.book;
  const bible = Array.isArray(source.bible) ? source.bible : [];
  const outlines = Array.isArray(source.outlines) ? source.outlines : [];
  const chapters = Array.isArray(source.chapters) ? source.chapters : [];
  const current =
    source.currentChapter !== null && typeof source.currentChapter === 'object'
      ? source.currentChapter
      : null;
  const existingContent = toText(source.existingContent);
  const instruction = toText(source.instruction).trim();
  const mode = source.mode === 'replace' ? 'replace' : 'append';
  const limits = resolveLimits(source.limits);

  // 复制后排序，绝不动入参。
  const sorted = chapters.slice().sort((a, b) => {
    const bySeq = seqOf(a) - seqOf(b);
    return bySeq !== 0 ? bySeq : idOf(a) - idOf(b);
  });
  const before = chaptersBefore(sorted, current);
  const previousChapter = before.length > 0 ? before[before.length - 1] : null;
  const allEarlier = before.length > 1 ? before.slice(0, before.length - 1) : [];
  const earlier =
    allEarlier.length > limits.maxEarlierChapters
      ? allEarlier.slice(allEarlier.length - limits.maxEarlierChapters)
      : allEarlier;

  const stats = {
    hasPreviousTail: false,
    previousChapterTitle: previousChapter === null ? null : chapterLabel(previousChapter),
    earlierCount: earlier.length,
    chaptersWithoutSummary: [],
    droppedEarlierCount: allEarlier.length - earlier.length,
  };

  const candidates = [
    buildBookBlock(book, limits),
    buildBibleBlock(bible, limits),
    buildPreviousBlock(previousChapter, earlier, limits, stats),
    buildOutlineBlock(outlines, current, limits),
    makeBlock('title', '本章标题', current === null ? '（未命名章节）' : chapterLabel(current)),
    makeBlock(
      'existing',
      '衔接正文',
      existingContent.trim() === ''
        ? ''
        : `（本章已有正文的末尾 ${limits.existingTailChars} 字，仅用于保持语气、人物与情节衔接，不要照抄这些句子）\n${takeTail(
            existingContent,
            limits.existingTailChars,
          )}`,
    ),
    toNumber(source.targetWords) === null
      ? null
      : makeBlock('target', '目标字数', `约 ${toNumber(source.targetWords)} 字（中文汉字计）。`),
    { key: 'task', label: '任务', content: taskText(mode), chars: taskText(mode).length },
    instruction === ''
      ? null
      : makeBlock('instruction', '额外要求', clipText(instruction, limits.instructionChars)),
  ];

  const blocks = candidates.filter(
    (block) => block !== null && block !== undefined && toText(block.content).trim() !== '',
  );
  const promptText = blocks.map((block) => block.content).join('\n\n');
  return { blocks, promptText, totalChars: promptText.length, stats };
}
