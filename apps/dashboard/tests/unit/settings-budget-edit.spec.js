// tests/unit/settings-budget-edit.spec.js — Phase 9.86 F78
import { describe, test, expect } from 'vitest';
import {
  BUDGET_EDIT_TARGETS,
  parseBudgetUsdInput,
  currentBudgetUsdForTarget,
} from '../../src/utils/settingsBudgetEdit.js';

describe('settingsBudgetEdit (F78)', () => {
  test('BUDGET_EDIT_TARGETS includes day/week and tiers', () => {
    const ids = BUDGET_EDIT_TARGETS.map((t) => t.id);
    expect(ids).toEqual(['day', 'week', 'haiku', 'sonnet', 'opus']);
  });

  test('parseBudgetUsdInput validates range', () => {
    expect(parseBudgetUsdInput('')).toEqual({ ok: false, message: '请输入预算金额 (USD)' });
    expect(parseBudgetUsdInput('-1')).toEqual({ ok: false, message: '金额须为 ≥ 0 的数字' });
    expect(parseBudgetUsdInput('10001')).toEqual({ ok: false, message: '金额不能超过 10000 USD' });
    expect(parseBudgetUsdInput('0.5')).toEqual({ ok: true, usd: 0.5 });
  });

  test('currentBudgetUsdForTarget reads window and tier values', () => {
    const dayTarget = BUDGET_EDIT_TARGETS[0];
    expect(
      currentBudgetUsdForTarget(dayTarget, { per_day: { budget_usd: 1.25 } }, {}),
    ).toBe(1.25);
    const sonnetTarget = BUDGET_EDIT_TARGETS[3];
    expect(
      currentBudgetUsdForTarget(sonnetTarget, {}, { sonnet: { usd: 2 } }),
    ).toBe(2);
  });
});
