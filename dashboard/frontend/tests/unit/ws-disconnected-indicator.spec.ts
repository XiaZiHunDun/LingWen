// tests/unit/ws-disconnected-indicator.spec.ts — Phase 8.30b + Phase 9.26 F10
// vitest — SidebarWsDisconnectedBanner WebSocket 断线 indicator
// Phase 9.26: 从 SidebarCostBanner 提升到 App sidebar 全局 (不依赖 hasCost).
//
// 契约:
//   - connected=false + hasMounted=true → 渲染 ws-disconnected-banner
//     (含中文 "实时同步已断开" + "页面数据可能过期", role="alert" +
//      aria-live="assertive")
//   - connected=true → banner 不显 (即使 hasMounted=true)
//   - hasMounted=false (mount 后 200ms 内) → banner 不显 (避免初次 mount flash)
//   - 0 依赖 cost props — 无成本数据时仍可见

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import SidebarWsDisconnectedBanner from '../../src/components/SidebarWsDisconnectedBanner.vue'
import { byTestid } from '../helpers/by-testid'

let connectedRef: ReturnType<typeof ref<boolean>>
vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({ connected: connectedRef }),
}))

describe('Sidebar WebSocket Disconnected Indicator (Phase 9.26 F10)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    connectedRef = ref(false)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  test('shows disconnected banner when WebSocket is closed (after 200ms gate)', async () => {
    const wrapper = mount(SidebarWsDisconnectedBanner)
    await flushPromises()

    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(false)

    vi.advanceTimersByTime(200)
    await flushPromises()

    const banner = wrapper.find(byTestid('ws-disconnected-banner'))
    expect(banner.exists()).toBe(true)
    expect(banner.text()).toContain('实时同步已断开')
    expect(banner.text()).toContain('页面数据可能过期')
    expect(banner.attributes('role')).toBe('alert')
    expect(banner.attributes('aria-live')).toBe('assertive')
  })

  test('hides disconnected banner when WebSocket is connected', async () => {
    connectedRef = ref(true)

    const wrapper = mount(SidebarWsDisconnectedBanner)
    await flushPromises()

    vi.advanceTimersByTime(200)
    await flushPromises()

    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(false)
  })

  test('shows banner without cost data (no hasCost gate)', async () => {
    const wrapper = mount(SidebarWsDisconnectedBanner)
    await flushPromises()

    vi.advanceTimersByTime(200)
    await flushPromises()

    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(true)
    expect(wrapper.find(byTestid('sidebar-cost-banner')).exists()).toBe(false)
  })
})
