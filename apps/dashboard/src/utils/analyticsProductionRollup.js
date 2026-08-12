/**
 * Phase 9.89 F81: Analytics production rollup from GET /api/production-records/rollup.
 */

/**
 * @typedef {Object} ProductionRollup
 * @property {number} record_count
 * @property {number} pilot_count
 * @property {number} batch_count
 * @property {number} total_cost_usd
 * @property {number} chapters_with_records
 * @property {string|null} [latest_recorded_at]
 * @property {Array<{ record_id: string, chapter_range?: string, total_cost_usd?: number, stopped_reason?: string, recorded_at?: string }>} [batches]
 */

/**
 * @param {ProductionRollup|null|undefined} rollup
 * @returns {Array<{ label: string, value: string|number }>}
 */
export function buildProductionRollupKpiCards(rollup) {
  if (!rollup || typeof rollup !== 'object') {
    return [
      { label: '生产记录', value: 0 },
      { label: 'Batch 数', value: 0 },
      { label: '累计成本 (USD)', value: '0.0000' },
      { label: '覆盖章节', value: 0 },
    ];
  }
  const cost = Number(rollup.total_cost_usd ?? 0);
  return [
    { label: '生产记录', value: rollup.record_count ?? 0 },
    { label: 'Batch 数', value: rollup.batch_count ?? 0 },
    { label: 'Pilot 文件', value: rollup.pilot_count ?? 0 },
    {
      label: '累计成本 (USD)',
      value: cost > 0 ? cost.toFixed(4) : '0.0000',
    },
    { label: '覆盖章节', value: rollup.chapters_with_records ?? 0 },
  ];
}

/**
 * @param {ProductionRollup|null|undefined} rollup
 * @returns {string[]}
 */
export function productionRollupSummaryLines(rollup) {
  if (!rollup?.latest_recorded_at) return [];
  return [
    `最近记录: ${rollup.latest_recorded_at.slice(0, 19)}`,
    rollup.batch_count > 0
      ? `Batch 汇总 ${rollup.batch_count} 条（成本已去重：batch 总计 + 非 batch 范围 pilot）`
      : '尚无 batch 记录',
  ];
}

/**
 * @param {ProductionRollup|null|undefined} rollup
 * @returns {Array<{ key: string, range: string, cost: string, status: string, at: string }>}
 */
export function formatBatchRollupRows(rollup) {
  const batches = rollup?.batches;
  if (!Array.isArray(batches) || !batches.length) return [];
  return batches.map((row) => ({
    key: row.record_id || row.source_file,
    range: row.chapter_range ? `ch${row.chapter_range}` : '-',
    cost:
      row.total_cost_usd != null
        ? `$${Number(row.total_cost_usd).toFixed(4)}`
        : '-',
    status: row.stopped_reason || '-',
    at: row.recorded_at ? row.recorded_at.slice(0, 19) : '-',
  }));
}
