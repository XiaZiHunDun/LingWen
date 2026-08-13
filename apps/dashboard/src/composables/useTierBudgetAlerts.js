/**
 * useTierBudgetAlerts.js — Tier budget alert log (Phase 9.27 F11)
 *
 * Module-level singleton alert log. Records tier threshold crossings
 * (warning >=80%, exceeded >=100%) with timestamp. Mirrors SidebarCostBanner
 * tier alarm thresholds (Phase 8.21).
 */

import { ref } from 'vue';

export const TIER_ORDER = ['haiku', 'sonnet', 'opus'];
export const TIER_ALARM_WARNING_PCT = 80;
export const TIER_ALARM_EXCEEDED_PCT = 100;
const MAX_ALERTS = 20;

const alerts = ref([]);
const prevTierLevels = {};
let alertSeq = 0;

function levelFromPct(pct) {
  if (pct >= TIER_ALARM_EXCEEDED_PCT) return 'exceeded';
  if (pct >= TIER_ALARM_WARNING_PCT) return 'warning';
  return 'ok';
}

/**
 * Compute per-tier budget level + pct for alert evaluation.
 * all-time: budget_by_tier.used_pct; windowed: windowed cost / budget.
 */
export function computeTierBudgetState({
  budgetByTier = {},
  timeWindow = 'all',
  windowedCostByTier = null,
}) {
  const states = {};
  for (const tierName of TIER_ORDER) {
    const entry = budgetByTier[tierName];
    if (!entry || entry.budget_usd == null) continue;

    let pct;
    if (timeWindow === 'all') {
      pct = Number(entry.used_pct ?? 0);
    } else {
      const used = Number(windowedCostByTier?.[tierName] ?? 0);
      const budgetUsd = Number(entry.budget_usd);
      if (budgetUsd <= 0) continue;
      pct = (used / budgetUsd) * 100;
    }

    states[tierName] = {
      level: levelFromPct(pct),
      pct: Math.round(pct * 10) / 10,
    };
  }
  return states;
}

/**
 * Append alert entries on tier level transitions (ok→warning, warning→exceeded, ok→exceeded).
 */
export function syncTierBudgetAlerts(states, timeWindow = 'all', now = new Date()) {
  for (const tierName of TIER_ORDER) {
    const state = states[tierName];
    const key = `${tierName}:${timeWindow}`;
    const nextLevel = state?.level ?? 'ok';
    const prevLevel = prevTierLevels[key] ?? 'ok';

    if (
      (nextLevel === 'warning' || nextLevel === 'exceeded')
      && prevLevel !== nextLevel
    ) {
      alertSeq += 1;
      alerts.value.unshift({
        id: alertSeq,
        tier: tierName,
        level: nextLevel,
        pct: state.pct,
        timeWindow,
        timestamp: now.toISOString(),
      });
      if (alerts.value.length > MAX_ALERTS) {
        alerts.value.length = MAX_ALERTS;
      }
    }

    prevTierLevels[key] = nextLevel;
  }
}

export function clearTierBudgetAlerts() {
  alerts.value = [];
  for (const key of Object.keys(prevTierLevels)) {
    delete prevTierLevels[key];
  }
  alertSeq = 0;
}

export function formatAlertTime(isoString) {
  const d = new Date(isoString);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

export function timeWindowLabel(timeWindow) {
  if (timeWindow === '7d') return '7天';
  if (timeWindow === '30d') return '30天';
  return '全部';
}

export function useTierBudgetAlerts() {
  return {
    alerts,
    clearAlerts: clearTierBudgetAlerts,
    syncTierBudgetAlerts,
    computeTierBudgetState,
    formatAlertTime,
    timeWindowLabel,
  };
}
