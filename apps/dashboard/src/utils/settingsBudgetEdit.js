/**
 * Phase 9.86 F78: budget edit targets for Settings write panel.
 */

/** @typedef {{ id: string, label: string, kind: 'window'|'tier', apiScope: string }} BudgetEditTarget */

/** @type {BudgetEditTarget[]} */
export const BUDGET_EDIT_TARGETS = [
  { id: 'day', label: '今日 (per-day)', kind: 'window', apiScope: 'day' },
  { id: 'week', label: '本周 (per-week)', kind: 'window', apiScope: 'week' },
  { id: 'haiku', label: 'Tier: haiku', kind: 'tier', apiScope: 'haiku' },
  { id: 'sonnet', label: 'Tier: sonnet', kind: 'tier', apiScope: 'sonnet' },
  { id: 'opus', label: 'Tier: opus', kind: 'tier', apiScope: 'opus' },
];

/**
 * @param {string} raw
 * @returns {{ ok: true, usd: number } | { ok: false, message: string }}
 */
export function parseBudgetUsdInput(raw) {
  const trimmed = String(raw ?? '').trim();
  if (!trimmed) {
    return { ok: false, message: '请输入预算金额 (USD)' };
  }
  const usd = Number(trimmed);
  if (!Number.isFinite(usd) || usd < 0) {
    return { ok: false, message: '金额须为 ≥ 0 的数字' };
  }
  if (usd > 10000) {
    return { ok: false, message: '金额不能超过 10000 USD' };
  }
  return { ok: true, usd };
}

/**
 * Resolve current USD for edit target from loaded API data.
 * @param {BudgetEditTarget} target
 * @param {Record<string, unknown>|null|undefined} windows
 * @param {Record<string, { usd?: number }|null|undefined>|null|undefined} tiers
 */
export function currentBudgetUsdForTarget(target, windows, tiers) {
  if (target.kind === 'window') {
    const key = target.apiScope === 'day' ? 'per_day' : 'per_week';
    const entry = windows?.[key];
    const budget = entry && typeof entry === 'object' ? entry.budget_usd : null;
    return budget != null ? Number(budget) : '';
  }
  const tierEntry = tiers?.[target.apiScope];
  return tierEntry?.usd != null ? Number(tierEntry.usd) : '';
}
