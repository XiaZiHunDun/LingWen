// tests/unit/settings-budget.spec.js — Phase 9.78 F68
import { describe, test, expect } from 'vitest'
import {
  formatWindowBudgetRows,
  formatTierBudgetRows,
  formatWsBudgetFallback,
} from '../../src/utils/settingsBudget.js'

describe('settingsBudget (F68)', () => {
  test('formatWindowBudgetRows skips empty entries', () => {
    const rows = formatWindowBudgetRows({
      per_run: { budget_usd: 1, used_usd: 0.5, used_pct: 50, status: 'ok' },
      per_day: {},
    })
    expect(rows).toHaveLength(1)
    expect(rows[0].label).toContain('per-run')
  })

  test('formatTierBudgetRows merges live usage', () => {
    const rows = formatTierBudgetRows(
      { haiku: { usd: 0.1, set_at: '2026-01-01' } },
      { haiku: { budget_usd: 0.1, used_usd: 0.02, used_pct: 20, status: 'ok' } },
    )
    expect(rows[0].used).toBe('0.0200')
    expect(rows[0].pct).toBe('20.0%')
  })

  test('formatWsBudgetFallback from status', () => {
    const rows = formatWsBudgetFallback({
      cost_budget_status: { budget_usd: 0.5, used_usd: 0.1, used_pct: 20, status: 'ok' },
    })
    expect(rows).toHaveLength(1)
  })
})
