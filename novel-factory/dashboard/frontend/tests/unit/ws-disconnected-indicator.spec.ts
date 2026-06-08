// tests/unit/ws-disconnected-indicator.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — SidebarCostBanner WebSocket 断线 indicator
// 跟 ceremonial Playwright spec (tests/e2e/ws-disconnected-indicator.spec.js)
// 同契约. 但用 @vue/test-utils + jsdom + vi.useFakeTimers 控 200ms setTimeout.
//
// 契约 (跟 ceremonial 同步):
//   - connected=false + hasMounted=true → 渲染 .ws-disconnected-banner
//     (含中文 "实时同步已断开" + "成本数据可能过期", role="alert" +
//      aria-live="assertive")
//   - connected=true → banner 不显 (即使 hasMounted=true)
//   - hasMounted=false (mount 后 200ms 内) → banner 不显 (避免初次 mount flash)
//   - 200ms setTimeout 用 vi.useFakeTimers 控, vi.advanceTimersByTime(200)

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import SidebarCostBanner from '../../src/components/SidebarCostBanner.vue'
import { byTestid } from '../helpers/by-testid'

const makeStatus = () => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 5,
  failed: 0,
  node_count: 7,
  steps: 12,
  cost_by_scenario: { chapter_writing: 0.025, chapter_review: 0.020 },
  cost_by_tier: {},
  total_cost_usd: 0.045,
})

// Phase 8.30b: mock useCostWindow 走 vue ref 保 reactivity
vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => {
    const timeWindow = ref('all')
    const windowedCost = ref(null)
    const setTimeWindow = vi.fn()
    return { timeWindow, windowedCost, setTimeWindow }
  },
}))

// Phase 8.30b: useWorkflowSocket mock 走 mutable ref (per test 配置 connected
// 值, 验证 banner gate 行为). 共享 mutable ref, vi.advanceTimersByTime 后
// 触发 isDisconnected computed re-eval.
let connectedRef: ReturnType<typeof ref<boolean>>
vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({ connected: connectedRef }),
}))

describe('Sidebar WebSocket Disconnected Indicator (Phase 8.27)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    connectedRef = ref(false)  // default: 模拟断线
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  test('shows disconnected banner when WebSocket is closed (after 200ms gate)', async () => {
    // connected=false (default beforeEach), hasMounted=false 初始 → banner 不显
    const wrapper = mount(SidebarCostBanner, {
      props: { status: makeStatus() },
    })
    await flushPromises()

    // 200ms 内: hasMounted=false → banner NOT visible
    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(false)

    // 推进 200ms → hasMounted=true + connected=false → banner 可见
    vi.advanceTimersByTime(200)
    await flushPromises()

    const banner = wrapper.find(byTestid('ws-disconnected-banner'))
    expect(banner.exists()).toBe(true)
    expect(banner.text()).toContain('实时同步已断开')
    expect(banner.text()).toContain('成本数据可能过期')
    // a11y: role="alert" + aria-live="assertive"
    expect(banner.attributes('role')).toBe('alert')
    expect(banner.attributes('aria-live')).toBe('assertive')
  })

  test('hides disconnected banner when WebSocket is connected', async () => {
    // connected=true (override default) → 即便 hasMounted=true, banner 不显
    connectedRef = ref(true)

    const wrapper = mount(SidebarCostBanner, {
      props: { status: makeStatus() },
    })
    await flushPromises()

    // 推进 200ms → hasMounted=true
    vi.advanceTimersByTime(200)
    await flushPromises()

    // connected=true → banner NOT visible
    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(false)
  })
})
