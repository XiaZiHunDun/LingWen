/**
 * Phase 9.97 F88: latest batch badge for ChaptersPage from production rollup.
 */

/**
 * @typedef {Object} BatchRollupItem
 * @property {string} [record_id]
 * @property {string|null} [chapter_range]
 * @property {number|null} [total_cost_usd]
 * @property {string|null} [stopped_reason]
 * @property {string|null} [recorded_at]
 * @property {string} [source_file]
 */

/**
 * @typedef {Object} ProductionRollup
 * @property {BatchRollupItem[]} [batches]
 */

/**
 * @param {BatchRollupItem[]|null|undefined} batches
 * @returns {BatchRollupItem|null}
 */
export function pickLatestBatch(batches) {
  if (!Array.isArray(batches) || !batches.length) return null;
  const sorted = [...batches].sort((a, b) => {
    const at = a.recorded_at || '';
    const bt = b.recorded_at || '';
    if (at !== bt) return bt.localeCompare(at);
    return (b.source_file || '').localeCompare(a.source_file || '');
  });
  return sorted[0] ?? null;
}

/**
 * @param {ProductionRollup|null|undefined} rollup
 * @returns {BatchRollupItem|null}
 */
export function latestBatchFromRollup(rollup) {
  return pickLatestBatch(rollup?.batches);
}

/**
 * @param {BatchRollupItem|null|undefined} batch
 * @returns {boolean}
 */
export function hasLatestBatchBadge(batch) {
  return Boolean(batch?.chapter_range);
}

/**
 * @param {BatchRollupItem|null|undefined} batch
 * @returns {string}
 */
export function formatLatestBatchBadge(batch) {
  if (!hasLatestBatchBadge(batch)) return '';
  const parts = [`ch${batch.chapter_range}`];
  if (batch.stopped_reason) parts.push(batch.stopped_reason);
  if (batch.recorded_at) parts.push(batch.recorded_at.slice(0, 10));
  if (batch.total_cost_usd != null) {
    parts.push(`$${Number(batch.total_cost_usd).toFixed(4)}`);
  }
  return parts.join(' · ');
}
