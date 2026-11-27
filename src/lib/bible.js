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
