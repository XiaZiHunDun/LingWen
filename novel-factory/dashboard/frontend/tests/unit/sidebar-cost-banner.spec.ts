// tests/unit/sidebar-cost-banner.spec.ts — Phase 8.30
// vitest 真 e2e 改造 — SidebarCostBanner 覆盖 Phase 8.27 (WS 断线) + Phase 8.28 (soft warning 三态)
// 跟 ceremonial specs (ws-disconnected-indicator.spec.js + soft-warning-state.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test, 不需 browser.
//
// 契约:
//   - Phase 8.27: connected=false + hasMounted=true → ⚠️ banner visible
//   - Phase 8.27: hasMounted=false (mount 200ms 内) → banner NOT visible (avoid flash)
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

describe('SidebarCostBanner: Phase 8.27 WS disconnected indicator', () => {
  test('shows disconnected banner when WebSocket is closed (after 200ms gate)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: { status: baseStatus() },
    })
    // connected 默认 false, hasMounted gate 是 200ms
    // 立即 query 看不到 banner (hasMounted=false)
    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(false)

    // 等 200ms gate 过, connected 仍 false → banner 出现
    await new Promise((r) => setTimeout(r, 250))
    await flushPromises()
    const banner = wrapper.find(byTestid('ws-disconnected-banner'))
    expect(banner.exists()).toBe(true)
    expect(banner.text()).toContain('实时同步已断开')
    expect(banner.text()).toContain('成本数据可能过期')
    expect(banner.attributes('role')).toBe('alert')
    expect(banner.attributes('aria-live')).toBe('assertive')
  })

  test('hides disconnected banner during initial 200ms mount gate (avoid flash)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: { status: baseStatus() },
    })
    // 立即 query (200ms 内) → banner 不可见 (gate 防初次 mount flash)
    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(false)
  })
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
})
