/**
 * Phase 9.78 F68: format budget rows for Settings read-only panel.
 */

const WINDOW_LABELS = {
  per_run: '单次运行 (per-run)',
  per_day: '今日 (per-day)',
  per_week: '本周 (per-week)',
};

const TIER_ORDER = ['haiku', 'sonnet', 'opus'];

/**
 * @param {Record<string, { budget_usd?: number, used_usd?: number, used_pct?: number, status?: string }|undefined>} windows
 * @returns {Array<{ key: string, label: string, budget: string, used: string, pct: string, status: string }>}
 */
export function formatWindowBudgetRows(windows) {
  if (!windows || typeof windows !== 'object') return [];
  return Object.entries(WINDOW_LABELS)
    .map(([key, label]) => {
      const entry = windows[key];
      if (!entry || entry.budget_usd == null) return null;
      return {
        key,
        label,
        budget: Number(entry.budget_usd).toFixed(4),
        used: Number(entry.used_usd ?? 0).toFixed(4),
        pct: `${Number(entry.used_pct ?? 0).toFixed(1)}%`,
        status: entry.status || 'ok',
      };
    })
    .filter(Boolean);
}

/**
 * @param {Record<string, { usd?: number, set_at?: string }|null|undefined>} tierLimits
 * @param {Record<string, { budget_usd?: number, used_usd?: number, used_pct?: number, status?: string }|undefined>} tierLive
 */
export function formatTierBudgetRows(tierLimits, tierLive) {
  const rows = [];
  for (const tier of TIER_ORDER) {
    const limit = tierLimits?.[tier];
    const live = tierLive?.[tier];
    const budgetUsd = live?.budget_usd ?? limit?.usd;
    if (budgetUsd == null) continue;
    rows.push({
      tier,
      label: tier,
      budget: Number(budgetUsd).toFixed(4),
      used: live?.used_usd != null ? Number(live.used_usd).toFixed(4) : '-',
      pct: live?.used_pct != null ? `${Number(live.used_pct).toFixed(1)}%` : '-',
      status: live?.status || 'ok',
      setAt: limit?.set_at || null,
    });
  }
  return rows;
}

/**
 * @param {Record<string, unknown>|null|undefined} status
 */
export function formatWsBudgetFallback(status) {
  if (!status) return [];
  return formatWindowBudgetRows({
    per_run: status.cost_budget_status,
    per_day: status.budget_per_day,
    per_week: status.budget_per_week,
  });
}
