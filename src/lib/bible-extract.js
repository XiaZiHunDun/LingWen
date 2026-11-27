/**
 * 设定集提取（纯函数）：组装「从本章正文抽取设定」的 prompt + 解析 LLM 返回的候选列表。
 *
 * 设计约束：
 *   1. 纯函数：不读环境变量、不访问网络 / 数据库、不修改入参、无随机与时间依赖；
 *   2. extract-bible 路由只做 IO（读章节、调 LLM、写日志），归一/去重/截断全在这里完成；
 *   3. 解析容错：允许 ```json 代码围栏、前后多余说明文字、单对象包数组、字段别名；
 *   4. 无法解析出 JSON 时抛错，错误信息以「模型输出不是合法 JSON」开头，由路由转成 502。
 */

/** 允许的设定分类（其它一律归「设定」）。 */
export const BIBLE_CATEGORIES = ['人物', '地点', '物品', '组织', '设定'];
/** 单次最多返回多少条候选。 */
export const MAX_CANDIDATES = 8;
/** title 最大字符数。 */
export const MAX_TITLE_CHARS = 20;
/** content 最大字符数。 */
export const MAX_CONTENT_CHARS = 80;
/** 拼 prompt 时正文最多带多少字，超出则截断并标注。 */
export const PROMPT_CONTENT_CHARS = 6000;
/** 拼 prompt 时最多列出多少条已有设定标题。 */
export const PROMPT_EXISTING_TITLES = 60;

/** 截断标记。 */
const ELLIPSIS = '…';

/** 分类别名 → 标准分类。 */
const CATEGORY_ALIASES = {
  角色: '人物',
  人物设定: '人物',
  人名: '人物',
  地名: '地点',
  场景: '地点',
  地方: '地点',
  位置: '地点',
  道具: '物品',
  物件: '物品',
  宝物: '物品',
  势力: '组织',
  团体: '组织',
  机构: '组织',
  门派: '组织',
  家族: '组织',
  世界观: '设定',
  背景: '设定',
  其它: '设定',
  其他: '设定',
};

/** 任意值 → 字符串（非字符串一律视为空）。 */
function toText(value) {
  return typeof value === 'string' ? value : '';
}

/** 空白压成单空格并去首尾空白。 */
function flatten(text) {
  return toText(text).replace(/\s+/g, ' ').trim();
}

/** 压空白后截断到 ≤ limit 字符（超出以「…」收尾）。 */
function clipText(text, limit) {
  const flat = flatten(text);
  if (flat.length <= limit) return flat;
  return `${flat.slice(0, Math.max(1, limit - ELLIPSIS.length))}${ELLIPSIS}`;
}

/** 去重用的归一化键：忽略空白与大小写。 */
function normalizeKey(text) {
  return flatten(text).replace(/\s+/g, '').toLowerCase();
}

/** 分类归一到 BIBLE_CATEGORIES 之内。 */
function normalizeCategory(value) {
  const raw = clipText(value, MAX_TITLE_CHARS);
  if (raw === '') return '设定';
  if (BIBLE_CATEGORIES.includes(raw)) return raw;
  const alias = CATEGORY_ALIASES[raw];
  return typeof alias === 'string' ? alias : '设定';
}

/**
 * 从模型输出里抠出 JSON 文本：去 ```json 围栏、去掉前后多余文字。
 *
 * @param {unknown} raw
 * @returns {string}
 */
function extractJsonText(raw) {
  const text = toText(raw).replace(/```[a-zA-Z0-9_-]*\s*/g, ' ').replace(/```/g, ' ');
  const start = text.search(/[[{]/);
  if (start === -1) return text.trim();
  const closer = text[start] === '[' ? ']' : '}';
  const end = text.lastIndexOf(closer);
  if (end <= start) return text.slice(start).trim();
  return text.slice(start, end + 1).trim();
}

/**
 * 组装设定提取的 system / user prompt。
 *
 * @param {{ chapterTitle?: unknown, content?: unknown, existingTitles?: unknown }} [params]
 * @returns {{ system: string, user: string }}
 */
export function buildBibleExtractPrompt({ chapterTitle, content, existingTitles } = {}) {
  const body = toText(content).trim();
  const truncated = body.length > PROMPT_CONTENT_CHARS;
  const excerpt = truncated
    ? `${body.slice(0, PROMPT_CONTENT_CHARS)}\n（正文已截断，以上为前 ${PROMPT_CONTENT_CHARS} 字）`
    : body;
  const chapter = flatten(chapterTitle) || '（未命名章节）';
  const titles = (Array.isArray(existingTitles) ? existingTitles : [])
    .map((item) => flatten(item))
    .filter((item) => item !== '')
    .slice(0, PROMPT_EXISTING_TITLES);

  const system = [
    '你是中文小说编辑，负责从章节正文中抽取可供后续写作复用的设定条目。',
    '硬性要求：',
    `1. 只输出一个 JSON 数组，不要输出解释、前后缀文字或 Markdown 代码块；最多 ${MAX_CANDIDATES} 项。`,
    '2. 每项形如 {"category":"人物","title":"林昭","content":"主角，城南镖局的少年镖师"}。',
    `3. category 只能是 ${BIBLE_CATEGORIES.join(' / ')} 之一；无法归类时填「设定」。`,
    `4. title 不超过 ${MAX_TITLE_CHARS} 字，只写名称本身；content 不超过 ${MAX_CONTENT_CHARS} 字，只写正文能支撑的信息。`,
    '5. 只提取正文中真实出现的人物、地点、物品、组织，不要编造，也不要推测正文未写明的内容。',
    '6. 下面给出的已有设定标题不要重复输出。',
  ].join('\n');

  const user = [
    `【章节标题】${chapter}`,
    `【已有设定标题】${titles.length === 0 ? '（暂无）' : titles.join('、')}`,
    `【章节正文】\n${excerpt === '' ? '（正文为空）' : excerpt}`,
    `请抽取本章新出现的设定，输出 JSON 数组（最多 ${MAX_CANDIDATES} 项），不要输出任何其它内容。`,
  ].join('\n\n');

  return { system, user };
}

/**
 * 解析模型输出为候选设定列表：解析 → 归一 → 按 title 去重（忽略空白/大小写）
 * → 过滤与已有设定重复的 → 截断 title/content → 最多 MAX_CANDIDATES 条。
 *
 * @param {unknown} raw 模型返回的原始文本
 * @param {unknown} [existingTitles] 本书已有设定标题
 * @returns {{ candidates: Array<{ category: string, title: string, content: string }>, skippedDuplicates: number }}
 */
export function parseBibleCandidates(raw, existingTitles = []) {
  const jsonText = extractJsonText(raw);

  let parsed;
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    throw new Error('模型输出不是合法 JSON：无法解析候选设定列表');
  }

  let list;
  if (Array.isArray(parsed)) {
    list = parsed;
  } else if (parsed !== null && typeof parsed === 'object') {
    const record = parsed;
    if (Array.isArray(record.candidates)) list = record.candidates;
    else if (Array.isArray(record.items)) list = record.items;
    else if (Array.isArray(record.data)) list = record.data;
    else if (typeof record.title === 'string') list = [record];
    else throw new Error('模型输出不是合法 JSON：顶层不是数组');
  } else {
    throw new Error('模型输出不是合法 JSON：顶层不是数组');
  }

  const seen = new Set();
  for (const title of Array.isArray(existingTitles) ? existingTitles : []) {
    const key = normalizeKey(title);
    if (key !== '') seen.add(key);
  }

  const candidates = [];
  let skippedDuplicates = 0;

  for (const item of list) {
    if (candidates.length >= MAX_CANDIDATES) break;
    if (item === null || typeof item !== 'object' || Array.isArray(item)) continue;

    const record = item;
    // 去重键基于「截断前」的原始标题：否则超长标题截断后会互相撞键，被误判为重复。
    const rawTitle = flatten(toText(record.title) || toText(record.name));
    if (rawTitle === '') continue;

    const key = normalizeKey(rawTitle);
    if (seen.has(key)) {
      skippedDuplicates += 1;
      continue;
    }
    seen.add(key);

    const title = clipText(rawTitle, MAX_TITLE_CHARS);

    const content = clipText(
      toText(record.content) || toText(record.description) || toText(record.desc) || toText(record.summary),
      MAX_CONTENT_CHARS,
    );

    candidates.push({ category: normalizeCategory(record.category), title, content });
  }

  return { candidates, skippedDuplicates };
}
