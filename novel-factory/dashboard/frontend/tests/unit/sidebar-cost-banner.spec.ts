// tests/unit/sidebar-cost-banner.spec.ts — Phase 8.30
// vitest 真 e2e 改造 — SidebarCostBanner 覆盖 Phase 8.28 (soft warning 三态)
// Phase 9.26 F10: WS 断线 indicator 移至 SidebarWsDisconnectedBanner (见 ws-disconnected-indicator.spec.ts)
//
// 契约:
//   - Phase 8.28: progress-bar-fill 3 态 (ok <80% / warning 80-100% / exceeded >=100%)
//   - 跟 Phase 8.21 tier alarm 阈值一致
//   - 0 改 backend cost_budget_status 二态语义

import { describe, test, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SidebarCostBanner from '../../src/components/SidebarCostBanner.vue'
import { byTestid } from '../helpers/by-testid'

const baseStatus = (overrides = {}) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  completed: 5,
  failed: 0,
  paused: false,
  paused_nodes: [],
  node_count: 7,
  steps: 5,
  total_cost_usd: 0.045,
  pending_decisions: [],
  executions: {},
  score_data: {},
  cost_by_scenario: { chapter_writing: 0.025, chapter_review: 0.020 },
  cost_by_tier: { haiku: 0.005, sonnet: 0.030, opus: 0.010 },
  ...overrides,
})

describe('SidebarCostBanner: Phase 8.28 soft warning three-state', () => {
  test('progress-bar-fill has .ok class when used_pct < 80%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          cost_budget_status: { status: 'ok', budget_usd: 0.10, used_usd: 0.020, used_pct: 20.0 },
        }),
      },
    })
    await flushPromises()
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('ok')
    expect(fill.classes()).not.toContain('warning')
    expect(fill.classes()).not.toContain('exceeded')
  })

  test('progress-bar-fill has .warning class when 80% <= used_pct < 100%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          cost_budget_status: { status: 'ok', budget_usd: 0.10, used_usd: 0.085, used_pct: 85.0 },
        }),
      },
    })
    await flushPromises()
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('warning')
    expect(fill.classes()).not.toContain('ok')
    expect(fill.classes()).not.toContain('exceeded')
  })

  test('progress-bar-fill has .exceeded class when used_pct >= 100%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          cost_budget_status: { status: 'exceeded', budget_usd: 0.10, used_usd: 0.120, used_pct: 120.0 },
        }),
      },
    })
    await flushPromises()
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('exceeded')
    expect(fill.classes()).not.toContain('ok')
    expect(fill.classes()).not.toContain('warning')
  })

  test('progress-bar-fill width style tracks used_pct', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          cost_budget_status: { status: 'ok', budget_usd: 0.10, used_usd: 0.045, used_pct: 45.0 },
        }),
      },
    })
    await flushPromises()
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.attributes('style')).toContain('width: 45%')
  })
})

describe('SidebarCostBanner: per-tier budget rows (Phase 8.15)', () => {
  test('renders 3 tier rows (haiku/sonnet/opus) when budget_by_tier set', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          budget_by_tier: {
            haiku: { budget_usd: 0.02, used_usd: 0.005, status: 'ok' },
            sonnet: { budget_usd: 0.05, used_usd: 0.030, status: 'ok' },
            opus: { budget_usd: 0.10, used_usd: 0.080, status: 'ok' },
          },
        }),
      },
    })
    await flushPromises()
    const tierRows = wrapper.findAll(byTestid('sidebar-cost-tier-row'))
    expect(tierRows.length).toBe(3)
  })

  test('hides tier row when tier budget not set (filter empty dict)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          budget_by_tier: {
            haiku: { budget_usd: 0.02, used_usd: 0.005, status: 'ok' },
            // sonnet 跳过
            opus: { budget_usd: 0.10, used_usd: 0.080, status: 'ok' },
          },
        }),
      },
    })
    await flushPromises()
    const tierRows = wrapper.findAll(byTestid('sidebar-cost-tier-row'))
    expect(tierRows.length).toBe(2)
  })

  test('tier-only cost shows banner without scenario entries', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          cost_by_scenario: {},
          cost_by_tier: { haiku: 0.01 },
        }),
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('sidebar-cost-banner')).exists()).toBe(true)
  })

  test('per-day exceeded budget wins cascade over per-run ok', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          cost_budget_status: { status: 'ok', budget_usd: 1, used_usd: 0.2, used_pct: 20 },
          budget_per_day: { status: 'exceeded', budget_usd: 1, used_usd: 1.2, used_pct: 120 },
        }),
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('sidebar-cost-budget-text')).text()).toContain('今日')
  })

  test('empty cost hides entire banner', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({ cost_by_scenario: {}, cost_by_tier: {} }),
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('sidebar-cost-banner')).exists()).toBe(false)
  })

  test('time window tab click invokes setTimeWindow', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ total_cost_usd: 0.01, cost_by_tier: { sonnet: 0.01 } }),
    }))
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: baseStatus({
          budget_by_tier: {
            sonnet: { budget_usd: 0.05, used_usd: 0.01, status: 'ok' },
          },
        }),
      },
    })
    await flushPromises()
    await wrapper.find(byTestid('sidebar-time-window-7d')).trigger('click')
    await flushPromises()
    expect(global.fetch).toHaveBeenCalled()
    vi.unstubAllGlobals()
  })
})
