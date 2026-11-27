/**
 * 章节状态（chapters.status）取值归一。
 *
 * 规则：
 *   - 空值（undefined / null / ''）→ 'draft'（历史数据没有 status 时按草稿处理）；
 *   - 'draft' / 'final' → 原样返回；
 *   - 其它任意值 → null（表示非法值，调用方应拒绝写入或回退到默认值）。
 *
 * 纯函数：不读写数据库、不抛错，前后端与测试共用同一套口径。
 *
 * @param {unknown} value
 * @returns {'draft' | 'final' | null}
 */
export function normalizeChapterStatus(value) {
  if (value === undefined || value === null) return 'draft';
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (trimmed === '') return 'draft';
  if (trimmed === 'draft' || trimmed === 'final') return trimmed;
  return null;
}

export default normalizeChapterStatus;
