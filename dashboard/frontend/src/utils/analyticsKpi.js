/**
 * Phase 9.77 F67: Analytics page KPI card builders (production + ripple).
 */

/**
 * @param {Record<string, unknown>|null|undefined} status
 * @returns {Array<{ label: string, value: string|number }>}
 */
export function buildProductionKpiCards(status) {
  const s = status || {};
  const pending = Array.isArray(s.pending_decisions) ? s.pending_decisions.length : 0;
  const cost = Number(s.total_cost_usd ?? 0);
  const summary = s.production_summary;
  const chapterNum =
    summary && typeof summary === 'object' && summary.chapter_num != null
      ? summary.chapter_num
      : null;

  return [
    {
      label: '工作流状态',
      value: s.is_active
        ? (s.paused ? `${s.workflow_name || '活跃'} · 暂停` : s.workflow_name || '运行中')
        : '空闲',
    },
    {
      label: '节点完成',
      value: s.is_active ? (s.completed ?? 0) : '-',
    },
    {
      label: '节点失败',
      value: s.is_active ? (s.failed ?? 0) : '-',
    },
    {
      label: 'LLM 成本 (USD)',
      value: cost > 0 ? cost.toFixed(4) : '0.0000',
    },
    {
      label: '待审决策',
      value: pending,
    },
    {
      label: '生产章节',
      value: chapterNum != null ? `#${chapterNum}` : '-',
    },
  ];
}

/**
 * @param {Record<string, unknown>|null|undefined} stats
 * @returns {Array<{ label: string, value: string|number }>}
 */
export function buildRippleKpiCards(stats) {
  const s = stats || {};
  const byStatus = s.by_status && typeof s.by_status === 'object' ? s.by_status : {};
  const open = byStatus.open ?? byStatus.OPEN ?? 0;
  const resolved = byStatus.resolved ?? byStatus.RESOLVED ?? 0;

  return [
    { label: '涟漪总数', value: s.total ?? 0 },
    { label: 'OPEN', value: open },
    { label: 'RESOLVED', value: resolved },
  ];
}
