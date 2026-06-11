// tests/unit/settings-page.spec.ts — Phase 9.78 F68
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SettingsPage from '../../src/pages/SettingsPage.vue'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  fetchBudgets: vi.fn(),
  fetchBudgetsByTier: vi.fn(),
  status: {
    value: {
      cost_budget_status: {},
      budget_by_tier: {
        sonnet: { budget_usd: 0.5, used_usd: 0.1, used_pct: 20, status: 'ok' },
      },
    },
  },
}))

vi.mock('../../src/api/index.js', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...(actual as object),
    fetchBudgets: mocks.fetchBudgets,
    fetchBudgetsByTier: mocks.fetchBudgetsByTier,
  }
})

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: mocks.status,
    connected: { value: true },
    lastError: { value: null },
  }),
}))

describe('SettingsPage (F68)', () => {
  beforeEach(() => {
    mocks.fetchBudgets.mockResolvedValue({
      per_run: { budget_usd: 1, used_usd: 0.2, used_pct: 20, status: 'ok' },
      per_day: {},
      per_week: {},
    })
    mocks.fetchBudgetsByTier.mockResolvedValue({
      haiku: null,
      sonnet: { usd: 0.5, set_at: '2026-06-11T00:00:00Z' },
      opus: null,
    })
  })

  test('renders title, budget tables, and env docs', async () => {
    const wrapper = mount(SettingsPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('系统设置')
    expect(wrapper.find(byTestid('budget-panel')).exists()).toBe(true)
    expect(wrapper.find(byTestid('window-budget-table')).exists()).toBe(true)
    expect(wrapper.find(byTestid('tier-budget-table')).exists()).toBe(true)
    expect(wrapper.find(byTestid('production-env-table')).text()).toContain('LINGWEN_REAL_LLM')
    expect(wrapper.find(byTestid('api-key-env-table')).text()).toContain('ANTHROPIC_API_KEY')
  })

  test('refresh reloads budget APIs', async () => {
    const wrapper = mount(SettingsPage)
    await flushPromises()
    mocks.fetchBudgets.mockClear()
    await wrapper.find(byTestid('refresh-btn')).trigger('click')
    await flushPromises()
    expect(mocks.fetchBudgets).toHaveBeenCalled()
  })
})
