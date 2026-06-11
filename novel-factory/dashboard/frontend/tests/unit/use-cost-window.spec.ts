// tests/unit/use-cost-window.spec.ts — Phase 9.57 F48
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'

describe('useCostWindow (F48 coverage)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
    window.history.replaceState(null, '', '/')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  async function mountHook() {
    const { useCostWindow } = await import('../../src/composables/useCostWindow.js')
    return mount(
      defineComponent({
        setup() {
          return useCostWindow()
        },
        template: '<div />',
      }),
    )
  }

  test('setTimeWindow all clears windowedCost without fetch body', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ total_cost_usd: 9 }),
    } as Response)
    const wrapper = await mountHook()
    wrapper.vm.setTimeWindow('7d')
    await flushPromises()
    wrapper.vm.setTimeWindow('all')
    await flushPromises()
    expect(wrapper.vm.windowedCost).toBeNull()
  })

  test('setTimeWindow 7d populates windowedCost', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        cost_by_scenario: { x: 1 },
        cost_by_tier: { t: 2 },
        cost_by_day: { '2026-06-01': 1 },
        cost_by_day_per_tier: null,
        total_cost_usd: 4.2,
      }),
    } as Response)
    const wrapper = await mountHook()
    wrapper.vm.setTimeWindow('7d')
    await flushPromises()
    expect(wrapper.vm.windowedCost?.total_cost_usd).toBe(4.2)
  })

  test('AbortError from fetch is ignored', async () => {
    vi.mocked(fetch).mockRejectedValue(new DOMException('Aborted', 'AbortError'))
    const wrapper = await mountHook()
    wrapper.vm.setTimeWindow('7d')
    await flushPromises()
    expect(wrapper.vm.lastError).toBeNull()
  })

  test('fetch HTTP error sets lastError', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 503 } as Response)
    const wrapper = await mountHook()
    wrapper.vm.setTimeWindow('30d')
    await flushPromises()
    expect(wrapper.vm.lastError).toContain('503')
  })

  test('invalid window ignored', async () => {
    const wrapper = await mountHook()
    wrapper.vm.setTimeWindow('bad')
    expect(wrapper.vm.timeWindow).toBe('all')
  })

  test('setTimeWindow writes URL param for 7d', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ total_cost_usd: 0 }),
    } as Response)
    const wrapper = await mountHook()
    wrapper.vm.setTimeWindow('7d')
    await flushPromises()
    expect(window.location.search).toContain('time_window=7d')
  })

  test('init reads valid time_window from URL', async () => {
    window.history.replaceState(null, '', '/?time_window=30d')
    vi.resetModules()
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ total_cost_usd: 0 }),
    } as Response)
    const { useCostWindow } = await import('../../src/composables/useCostWindow.js')
    const wrapper = mount(defineComponent({
      setup() { return useCostWindow() },
      template: '<div />',
    }))
    await flushPromises()
    expect(wrapper.vm.timeWindow).toBe('30d')
  })

  test('init ignores invalid URL time_window', async () => {
    window.history.replaceState(null, '', '/?time_window=bad')
    vi.resetModules()
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ total_cost_usd: 0 }),
    } as Response)
    const { useCostWindow } = await import('../../src/composables/useCostWindow.js')
    const wrapper = mount(defineComponent({
      setup() { return useCostWindow() },
      template: '<div />',
    }))
    await flushPromises()
    expect(wrapper.vm.timeWindow).toBe('all')
  })
})
