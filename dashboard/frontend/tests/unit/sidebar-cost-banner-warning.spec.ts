// tests/unit/sidebar-cost-banner-warning.spec.ts — Phase 9.57 F48
import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => ({
    timeWindow: { value: '30d' },
    windowedCost: {
      value: {
        cost_by_tier: { haiku: 0.085 },
        cost_by_scenario: {},
        total_cost_usd: 0.085,
      },
    },
    setTimeWindow: vi.fn(),
  }),
}))

import SidebarCostBanner from '../../src/components/SidebarCostBanner.vue'

describe('SidebarCostBanner warning alarm (F48)', () => {
  test('shows warning alarm between 80-100%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: {
          workflow_name: 'wf',
          is_active: true,
          cost_by_scenario: { x: 0.01 },
          cost_by_tier: { haiku: 0.01 },
          total_cost_usd: 0.085,
          budget_by_tier: {
            haiku: { budget_usd: 0.1, used_usd: 0.01, status: 'ok' },
          },
        },
      },
    })
    await flushPromises()
    const alarm = wrapper.find(byTestid('sidebar-tier-alarm-haiku'))
    expect(alarm.exists()).toBe(true)
    expect(alarm.text()).toContain('⚠️')
  })
})
