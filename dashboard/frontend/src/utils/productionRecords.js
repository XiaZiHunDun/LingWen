/**
 * Phase 9.82 F74: format production record rows for ChaptersPage history panel.
 */

/**
 * @typedef {Object} ProductionRecord
 * @property {string} record_id
 * @property {'pilot'|'batch'} record_type
 * @property {number|null} [chapter_num]
 * @property {string|null} [chapter_range]
 * @property {string|null} [operator]
 * @property {string|null} [recorded_at]
 * @property {string|null} [provider]
 * @property {number|null} [total_cost_usd]
 * @property {boolean|null} [emit_chapter_completed]
 * @property {string|null} [memory_context_source]
 * @property {string|null} [stopped_reason]
 * @property {string} source_file
 */

/**
 * @param {ProductionRecord} record
 * @returns {string}
 */
export function formatRecordCost(record) {
  if (record.total_cost_usd == null) return '-';
  return `$${Number(record.total_cost_usd).toFixed(4)}`;
}

/**
 * @param {ProductionRecord} record
 * @returns {string}
 */
export function formatRecordChapterLabel(record) {
  if (record.record_type === 'batch' && record.chapter_range) {
    return `ch${record.chapter_range}`;
  }
  if (record.chapter_num != null) {
    return `#${record.chapter_num}`;
  }
  return '-';
}

/**
 * @param {ProductionRecord} record
 * @returns {string}
 */
export function formatRecordStatus(record) {
  if (record.record_type === 'batch') {
    return record.stopped_reason || 'batch';
  }
  if (record.emit_chapter_completed === true) return 'emit ok';
  if (record.emit_chapter_completed === false) return 'emit fail';
  return '-';
}

/**
 * @param {ProductionRecord} record
 * @returns {string}
 */
export function formatRecordSummaryLine(record) {
  const parts = [
    formatRecordChapterLabel(record),
    record.record_type,
    formatRecordCost(record),
  ];
  if (record.provider) parts.push(record.provider);
  if (record.memory_context_source) parts.push(`mem:${record.memory_context_source}`);
  parts.push(formatRecordStatus(record));
  return parts.join(' · ');
}

/**
 * @param {ProductionRecord[]} records
 * @returns {Record<number, ProductionRecord>}
 */
export function indexRecordsByChapter(records) {
  /** @type {Record<number, ProductionRecord>} */
  const map = {};
  for (const rec of records) {
    if (rec.record_type === 'pilot' && rec.chapter_num != null) {
      if (!map[rec.chapter_num]) map[rec.chapter_num] = rec;
      continue;
    }
    if (rec.record_type === 'batch' && rec.chapter_range) {
      const parts = rec.chapter_range.split('-');
      const lo = Number(parts[0]);
      const hi = Number(parts[parts.length - 1]);
      if (!Number.isNaN(lo) && !Number.isNaN(hi)) {
        for (let ch = lo; ch <= hi; ch += 1) {
          if (!map[ch]) map[ch] = rec;
        }
      }
    }
  }
  return map;
}

/**
 * @param {number} chapterNum
 * @param {Record<number, ProductionRecord>} byChapter
 * @returns {string|null}
 */
export function chapterProductionBadge(chapterNum, byChapter) {
  const rec = byChapter[chapterNum];
  if (!rec) return null;
  if (rec.record_type === 'pilot') {
    return rec.emit_chapter_completed ? '已生产' : '生产异常';
  }
  return 'batch';
}

/**
 * @param {ProductionRecord[]} records
 * @returns {Array<{ key: string, chapter: string, type: string, cost: string, provider: string, memory: string, status: string, operator: string, at: string }>}
 */
export function formatProductionRecordRows(records) {
  return records.map((rec) => ({
    key: rec.record_id || rec.source_file,
    chapter: formatRecordChapterLabel(rec),
    type: rec.record_type,
    cost: formatRecordCost(rec),
    provider: rec.provider || '-',
    memory: rec.memory_context_source || '-',
    status: formatRecordStatus(rec),
    operator: rec.operator || '-',
    at: rec.recorded_at ? rec.recorded_at.slice(0, 19) : '-',
  }));
}
