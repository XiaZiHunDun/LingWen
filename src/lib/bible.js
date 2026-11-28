/**
 * 设定集条目编辑的纯校验逻辑（不碰数据库，便于单测）。
 *
 * 约定：PATCH /api/bible/[id] 的 body 允许 category / title / content 的任意子集，
 * 未知 key 一律忽略；只把 trim 后的合法字段放进 values。
 */

export const BIBLE_LIMITS = {
  title: 40,
  category: 20,
  content: 500,
};

/** 按字符（而非 UTF-16 code unit）计算长度，中文/emoji 均算 1 字。 */
function charLength(value) {
  return [...value].length;
}

/**
 * 归一化设定集条目的 PATCH body。
 *
 * 返回约定：
 *   - 成功：{ values: { category?, title?, content? }, error: null }
 *     values 里只包含本次真正要更新的字段，且字符串均已按规则处理；
 *   - 失败：{ values: {}, error: '错误信息' }
 *
 * @param {unknown} body 已解析的请求体
 * @returns {{ values: { category?: string, title?: string, content?: string }, error: string | null }}
 */
export function normalizeBiblePatch(body) {
  const source = body !== null && typeof body === 'object' ? body : {};

  /** @type {{ category?: string, title?: string, content?: string }} */
  const values = {};
  let hasField = false;

  if (Object.prototype.hasOwnProperty.call(source, 'category')) {
    const raw = source.category;
    if (typeof raw !== 'string') {
      return { values: {}, error: '分类必须是字符串' };
    }
    const category = raw.trim();
    if (charLength(category) > BIBLE_LIMITS.category) {
      return { values: {}, error: `分类不能超过 ${BIBLE_LIMITS.category} 字` };
    }
    values.category = category;
    hasField = true;
  }

  if (Object.prototype.hasOwnProperty.call(source, 'title')) {
    const raw = source.title;
    if (typeof raw !== 'string') {
      return { values: {}, error: '标题必须是字符串' };
    }
    const title = raw.trim();
    if (title === '') {
      return { values: {}, error: '标题不能为空' };
    }
    if (charLength(title) > BIBLE_LIMITS.title) {
      return { values: {}, error: `标题不能超过 ${BIBLE_LIMITS.title} 字` };
    }
    values.title = title;
    hasField = true;
  }

  if (Object.prototype.hasOwnProperty.call(source, 'content')) {
    const raw = source.content;
    if (typeof raw !== 'string') {
      return { values: {}, error: '内容必须是字符串' };
    }
    if (charLength(raw) > BIBLE_LIMITS.content) {
      return { values: {}, error: `内容不能超过 ${BIBLE_LIMITS.content} 字` };
    }
    values.content = raw.trim() === '' ? '' : raw;
    hasField = true;
  }

  if (!hasField) {
    return { values: {}, error: '没有可更新的字段' };
  }

  return { values, error: null };
}

/**
 * 设定改名的「全书同步替换」纯函数（不碰数据库，便于单测）。
 *
 * 匹配口径与 src/lib/find-replace.js 完全一致：区分大小写的**字面量**匹配，
 * 逐个非重叠命中，绝不做正则解释；from 为空串 / 非字符串 / from === to 时
 * 一律视为 0 命中、value 原样返回（避免「空串命中每处」的危险替换）。
 */

/**
 * 把 text 中的字面量 from 全部换成 to，并统计命中次数。
 * @param {unknown} text 原文（非字符串按空串处理）
 * @param {unknown} from 查找词
 * @param {unknown} to 替换词
 * @returns {{ value: string, count: number }} count 为 0 时 value 与原文完全一致
 */
export function replaceAllCount(text, from, to) {
  const source = typeof text === 'string' ? text : '';
  // from 为空 / 非字符串 / 新旧相同：0 处，原样返回。
  if (typeof from !== 'string' || from === '' || from === to) {
    return { value: source, count: 0 };
  }
  const next = typeof to === 'string' ? to : '';

  let count = 0;
  let index = source.indexOf(from);
  while (index !== -1) {
    count += 1;
    index = source.indexOf(from, index + from.length);
  }
  if (count === 0) return { value: source, count: 0 };
  return { value: source.split(from).join(next), count };
}

/**
 * 生成「设定改名 → 全书同步替换」的变更计划（纯读入参，不写库）。
 *
 * 由路由在事务里按计划执行：章节正文/标题、大纲标题/摘要。
 * 只有真正命中的条数才进计划，因此 plan.chapters/plan.outlines 的长度
 * 就是「被改动的条数」，plan.occurrences 是总命中次数（同一字段多次命中都计入）。
 *
 * 说明：from 按 trim 后的值参与匹配（设定标题入库前已 trim），to 原样使用。
 *
 * @param {{ chapters?: Array<Record<string, unknown>>, outlines?: Array<Record<string, unknown>> }} input
 * @param {unknown} from 旧标题
 * @param {unknown} to 新标题
 * @returns {{
 *   from: string,
 *   to: string,
 *   chapters: Array<{
 *     id: number, seq: number|null,
 *     titleBefore: string, titleAfter: string,
 *     contentBefore: string, contentAfter: string,
 *     titleChanged: boolean, contentChanged: boolean,
 *     titleOccurrences: number, contentOccurrences: number, occurrences: number,
 *   }>,
 *   outlines: Array<{
 *     id: number, seq: number|null,
 *     titleBefore: string, titleAfter: string,
 *     summaryBefore: string, summaryAfter: string,
 *     titleChanged: boolean, summaryChanged: boolean,
 *     titleOccurrences: number, summaryOccurrences: number, occurrences: number,
 *   }>,
 *   chapterCount: number, outlineCount: number, occurrences: number,
 * }}
 */
export function collectRenameChanges(input, from, to) {
  const source = input !== null && typeof input === 'object' ? input : {};
  const chapterList = Array.isArray(source.chapters) ? source.chapters : [];
  const outlineList = Array.isArray(source.outlines) ? source.outlines : [];
  const oldName = typeof from === 'string' ? from.trim() : '';
  const newName = typeof to === 'string' ? to : '';

  /** @type {ReturnType<typeof collectRenameChanges>} */
  const plan = {
    from: oldName,
    to: newName,
    chapters: [],
    outlines: [],
    chapterCount: 0,
    outlineCount: 0,
    occurrences: 0,
  };

  // 旧名为空 / 新旧相同：0 处，不产生任何变更。
  if (oldName === '' || oldName === newName) return plan;

  for (const chapter of chapterList) {
    if (chapter === null || typeof chapter !== 'object') continue;
    const id = Number(chapter.id ?? chapter.chapterId);
    if (!Number.isFinite(id)) continue;
    const titleBefore = typeof chapter.title === 'string' ? chapter.title : '';
    const contentBefore = typeof chapter.content === 'string' ? chapter.content : '';
    const titleResult = replaceAllCount(titleBefore, oldName, newName);
    const contentResult = replaceAllCount(contentBefore, oldName, newName);
    const occurrences = titleResult.count + contentResult.count;
    if (occurrences === 0) continue;
    plan.chapters.push({
      id,
      seq: typeof chapter.seq === 'number' ? chapter.seq : null,
      titleBefore,
      titleAfter: titleResult.value,
      contentBefore,
      contentAfter: contentResult.value,
      titleChanged: titleResult.count > 0,
      contentChanged: contentResult.count > 0,
      titleOccurrences: titleResult.count,
      contentOccurrences: contentResult.count,
      occurrences,
    });
  }

  for (const outline of outlineList) {
    if (outline === null || typeof outline !== 'object') continue;
    const id = Number(outline.id ?? outline.outlineId);
    if (!Number.isFinite(id)) continue;
    const titleBefore = typeof outline.title === 'string' ? outline.title : '';
    const summaryBefore = typeof outline.summary === 'string' ? outline.summary : '';
    const titleResult = replaceAllCount(titleBefore, oldName, newName);
    const summaryResult = replaceAllCount(summaryBefore, oldName, newName);
    const occurrences = titleResult.count + summaryResult.count;
    if (occurrences === 0) continue;
    plan.outlines.push({
      id,
      seq: typeof outline.seq === 'number' ? outline.seq : null,
      titleBefore,
      titleAfter: titleResult.value,
      summaryBefore,
      summaryAfter: summaryResult.value,
      titleChanged: titleResult.count > 0,
      summaryChanged: summaryResult.count > 0,
      titleOccurrences: titleResult.count,
      summaryOccurrences: summaryResult.count,
      occurrences,
    });
  }

  plan.chapterCount = plan.chapters.length;
  plan.outlineCount = plan.outlines.length;
  plan.occurrences =
    plan.chapters.reduce((sum, item) => sum + item.occurrences, 0) +
    plan.outlines.reduce((sum, item) => sum + item.occurrences, 0);

  return plan;
}
