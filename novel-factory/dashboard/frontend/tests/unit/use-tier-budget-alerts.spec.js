// tests/unit/use-tier-budget-alerts.spec.js — Phase 9.27 F11
import { describe, test, expect, beforeEach } from 'vitest';
import {
  computeTierBudgetState,
  syncTierBudgetAlerts,
  clearTierBudgetAlerts,
  formatAlertTime,
  timeWindowLabel,
  useTierBudgetAlerts,
} from '../../src/composables/useTierBudgetAlerts.js';

describe('useTierBudgetAlerts (Phase 9.27 F11)', () => {
  beforeEach(() => {
    clearTierBudgetAlerts();
  });

  test('computeTierBudgetState uses used_pct for all-time window', () => {
    const states = computeTierBudgetState({
      budgetByTier: {
        opus: { budget_usd: 1.0, used_usd: 1.2, used_pct: 120.0 },
        haiku: { budget_usd: 0.1, used_usd: 0.05, used_pct: 50.0 },
      },
      timeWindow: 'all',
    });
    expect(states.opus).toEqual({ level: 'exceeded', pct: 120 });
    expect(states.haiku).toEqual({ level: 'ok', pct: 50 });
  });

  test('computeTierBudgetState uses windowed cost for 7d window', () => {
    const states = computeTierBudgetState({
      budgetByTier: {
        sonnet: { budget_usd: 0.5, used_usd: 0.1, used_pct: 20.0 },
      },
      timeWindow: '7d',
      windowedCostByTier: { sonnet: 0.45 },
    });
    expect(states.sonnet).toEqual({ level: 'warning', pct: 90 });
  });

  test('syncTierBudgetAlerts logs on threshold transition with timestamp', () => {
    const now = new Date('2026-06-11T14:32:00+08:00');
    syncTierBudgetAlerts(
      { opus: { level: 'exceeded', pct: 120 } },
      'all',
      now,
    );

    const { alerts } = useTierBudgetAlerts();
    expect(alerts.value).toHaveLength(1);
    expect(alerts.value[0]).toMatchObject({
      tier: 'opus',
      level: 'exceeded',
      pct: 120,
      timeWindow: 'all',
      timestamp: now.toISOString(),
    });
  });

  test('syncTierBudgetAlerts does not duplicate while level unchanged', () => {
    const states = { opus: { level: 'exceeded', pct: 120 } };
    syncTierBudgetAlerts(states, 'all', new Date('2026-06-11T10:00:00Z'));
    syncTierBudgetAlerts(states, 'all', new Date('2026-06-11T10:05:00Z'));

    const { alerts } = useTierBudgetAlerts();
    expect(alerts.value).toHaveLength(1);
  });

  test('syncTierBudgetAlerts logs warning then exceeded escalation', () => {
    syncTierBudgetAlerts(
      { sonnet: { level: 'warning', pct: 85 } },
      '7d',
      new Date('2026-06-11T10:00:00Z'),
    );
    syncTierBudgetAlerts(
      { sonnet: { level: 'exceeded', pct: 105 } },
      '7d',
      new Date('2026-06-11T10:01:00Z'),
    );

    const { alerts } = useTierBudgetAlerts();
    expect(alerts.value).toHaveLength(2);
    expect(alerts.value[0].level).toBe('exceeded');
    expect(alerts.value[1].level).toBe('warning');
  });

  test('formatAlertTime and timeWindowLabel helpers', () => {
    expect(formatAlertTime('2026-06-11T14:32:00+08:00')).toMatch(/^\d{2}:\d{2}$/);
    expect(timeWindowLabel('7d')).toBe('7天');
    expect(timeWindowLabel('all')).toBe('全部');
  });
});
