/**
 * Phase 9.74 F66: shared formatting for chapter production observability.
 */

/**
 * @param {Record<string, unknown>|null|undefined} bf
 * @returns {string}
 */
export function formatIncrementalBackfill(bf) {
  if (!bf || typeof bf !== 'object') return '';
  const parts = [];
  if (bf.nodes_written != null) parts.push(`写入 ${bf.nodes_written} 节点`);
  if (bf.nodes_skipped != null) parts.push(`跳过 ${bf.nodes_skipped}`);
  if (bf.total_count != null) parts.push(`抽取 ${bf.total_count}`);
  if (bf.elapsed_s != null) parts.push(`${Number(bf.elapsed_s).toFixed(2)}s`);
  return parts.length ? parts.join(' · ') : JSON.stringify(bf);
}

/**
 * @param {Record<string, unknown>|null|undefined} summary
 * @returns {string[]}
 */
export function productionSummaryLines(summary) {
  if (!summary || typeof summary !== 'object') return [];
  const lines = [];
  if (summary.chapter_num != null) {
    lines.push(`章节 #${summary.chapter_num}`);
  }
  if (summary.memory_context_source) {
    lines.push(`Memory: ${summary.memory_context_source}`);
  }
  if (summary.emit_chapter_completed === true) {
    lines.push('emit_chapter 已完成');
  } else if (summary.emit_chapter_completed === false) {
    lines.push('emit_chapter 未完成');
  }
  const bfLabel = formatIncrementalBackfill(
    /** @type {Record<string, unknown>} */ (summary.incremental_backfill),
  );
  if (bfLabel) {
    lines.push(`Backfill: ${bfLabel}`);
  }
  return lines;
}

/**
 * Prefer nested production_summary; fall back to top-level incremental_backfill.
 * @param {Record<string, unknown>|null|undefined} status
 * @returns {Record<string, unknown>|null}
 */
export function resolveProductionSummary(status) {
  if (!status || typeof status !== 'object') return null;
  const nested = status.production_summary;
  if (nested && typeof nested === 'object') return nested;
  const bf = status.incremental_backfill;
  if (bf && typeof bf === 'object') {
    return { incremental_backfill: bf };
  }
  return null;
}

/**
 * @param {Record<string, unknown>|null|undefined} status
 * @returns {boolean}
 */
export function hasProductionSummary(status) {
  const summary = resolveProductionSummary(status);
  if (!summary) return false;
  return productionSummaryLines(summary).length > 0;
}
