/**
 * 设定集搜索与分类筛选的纯函数（不碰数据库，便于单测）。
 *
 * 约定：
 *   - query 先 trim；为空则不做关键词过滤；否则在 title / content / category
 *     三个字段做大小写不敏感的包含匹配；
 *   - category 为空/未传 → 不过滤；否则只保留 trim 后完全相等的条目；
 *   - 两个条件叠加，保持输入顺序，不改动任何字段。
 */

/** 把任意值安全转成字符串（非字符串一律视为空串）。 */
function text(value) {
  return typeof value === 'string' ? value : '';
}

/**
 * 按关键词与分类筛选设定条目。
 *
 * @param {unknown} items 设定条目数组
 * @param {{ query?: string | null, category?: string | null }} [options]
 * @returns {any[]} 命中条目（原对象引用），非数组输入返回空数组
 */
export function filterBibleItems(items, options) {
  if (!Array.isArray(items)) return [];
  const opts = options !== null && typeof options === 'object' ? options : {};
  const query = typeof opts.query === 'string' ? opts.query.trim() : '';
  const category = typeof opts.category === 'string' ? opts.category.trim() : '';
  const needle = query.toLowerCase();

  const result = [];
  for (const item of items) {
    if (item === null || typeof item !== 'object' || Array.isArray(item)) continue;
    if (category !== '' && text(item.category).trim() !== category) continue;
    if (needle !== '') {
      const haystack = `${text(item.title)}\n${text(item.content)}\n${text(item.category)}`;
      if (!haystack.toLowerCase().includes(needle)) continue;
    }
    result.push(item);
  }
  return result;
}

/**
 * 收集所有非空分类，去重并按中文排序。
 *
 * @param {unknown} items 设定条目数组
 * @returns {string[]}
 */
export function collectBibleCategories(items) {
  if (!Array.isArray(items)) return [];
  const seen = new Set();
  for (const item of items) {
    if (item === null || typeof item !== 'object' || Array.isArray(item)) continue;
    const category = text(item.category).trim();
    if (category !== '') seen.add(category);
  }
  return [...seen].sort((a, b) => a.localeCompare(b, 'zh'));
}
