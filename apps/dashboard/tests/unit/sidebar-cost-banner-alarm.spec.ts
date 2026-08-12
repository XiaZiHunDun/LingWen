// tests/unit/sidebar-cost-banner-alarm.spec.ts — Phase 9.57 F48
import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => ({
    timeWindow: { value: '7d' },
    windowedCost: {
      value: {
        cost_by_tier: { sonnet: 0.09 },
        cost_by_scenario: {},
        total_cost_usd: 0.09,
      },
    },
    setTimeWindow: vi.fn(),
  }),
}))

import SidebarCostBanner from '../../src/components/SidebarCostBanner.vue'

const baseStatus = {
  workflow_name: 'wf',
  is_active: true,
  cost_by_scenario: { x: 0.01 },
  cost_by_tier: { sonnet: 0.01 },
  total_cost_usd: 0.09,
  budget_by_tier: {
    sonnet: { budget_usd: 0.1, used_usd: 0.01, status: 'ok' },
  },
}

describe('SidebarCostBanner tier alarms (F48)', () => {
  test('shows exceeded alarm when windowed tier over budget', async () => {
    const wrapper = mount(SidebarCostBanner, { props: { status: baseStatus } })
    await flushPromises()
    expect(wrapper.find(byTestid('sidebar-tier-alarm-sonnet')).exists()).toBe(true)
  })
})
