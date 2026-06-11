// tests/unit/use-decision-store.spec.ts — Phase 8.34
// useDecisionStore module-level singleton test
// 镜像 useWorkflowSocket 测试隔离模式:
//   vi.mock(...) at top, vi.resetModules() + dynamic import per test
//   to avoid state contamination between tests.
import { beforeEach, describe, expect, test, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('../../src/api/index.js', () => ({
  fetchAllDecisions: vi.fn(),
  resolveDecision: vi.fn(),
  deferDecision: vi.fn(),
  cancelDecision: vi.fn(),
}))

let useDecisionStore: typeof import('../../src/composables/useDecisionStore.js').useDecisionStore
let api: typeof import('../../src/api/index.js')

beforeEach(async () => {
  vi.resetModules()
  api = await import('../../src/api/index.js')
  vi.mocked(api.fetchAllDecisions).mockReset()
  vi.mocked(api.resolveDecision).mockReset()
  vi.mocked(api.deferDecision).mockReset()
  vi.mocked(api.cancelDecision).mockReset()
  vi.mocked(api.fetchAllDecisions).mockResolvedValue([])
  vi.mocked(api.resolveDecision).mockResolvedValue({})
  vi.mocked(api.deferDecision).mockResolvedValue({})
  vi.mocked(api.cancelDecision).mockResolvedValue({})
  const mod = await import('../../src/composables/useDecisionStore.js')
  useDecisionStore = mod.useDecisionStore
})

function mountStore() {
  const Harness = defineComponent({
    setup() {
      return useDecisionStore()
    },
    render() { return h('div') },
  })
  return mount(Harness)
}

describe('useDecisionStore — Phase 8.34 module-level singleton', () => {
  test('initial state: all=[], loading=false, lastError=null', () => {
    const wrapper = mountStore()
    const s = wrapper.vm as unknown as {
      all: unknown[]; loading: boolean; lastError: string | null
    }
    expect(s.all).toEqual([])
    expect(s.loading).toBe(false)
    expect(s.lastError).toBeNull()
  })

  test('refresh populates all from fetchAllDecisions', async () => {
    vi.mocked(api.fetchAllDecisions).mockResolvedValue([
      { decision_id: 'd1', status: 'pending' },
      { decision_id: 'd2', status: 'resolved' },
    ])
    const wrapper = mountStore()
    await flushPromises()
    const s = wrapper.vm as unknown as { all: Array<{ decision_id: string }> }
    expect(api.fetchAllDecisions).toHaveBeenCalledTimes(1)
    expect(s.all.length).toBe(2)
    expect(s.all[0].decision_id).toBe('d1')
  })

  test('resolve calls API + refreshes all', async () => {
    const updated = [{ decision_id: 'd1', status: 'resolved' }]
    vi.mocked(api.resolveDecision).mockResolvedValue({ decision_id: 'd1' })
    vi.mocked(api.fetchAllDecisions)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(updated)
    const wrapper = mountStore()
    await flushPromises()
    await (wrapper.vm as unknown as {
      resolve: (id: string, opt: string) => Promise<void>
    }).resolve('d1', 'option_a')
    await flushPromises()
    expect(api.resolveDecision).toHaveBeenCalledWith('d1', 'option_a')
    expect(api.fetchAllDecisions).toHaveBeenCalledTimes(2)
    const s = wrapper.vm as unknown as { all: Array<{ decision_id: string; status: string }> }
    expect(s.all[0].status).toBe('resolved')
  })

  test('defer calls API + refreshes all', async () => {
    const updated = [{ decision_id: 'd1', status: 'deferred' }]
    vi.mocked(api.deferDecision).mockResolvedValue({ decision_id: 'd1' })
    vi.mocked(api.fetchAllDecisions)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(updated)
    const wrapper = mountStore()
    await flushPromises()
    await (wrapper.vm as unknown as {
      defer: (id: string, reason: string) => Promise<void>
    }).defer('d1', 'reason text')
    await flushPromises()
    expect(api.deferDecision).toHaveBeenCalledWith('d1', 'reason text')
    const s = wrapper.vm as unknown as { all: Array<{ status: string }> }
    expect(s.all[0].status).toBe('deferred')
  })

  test('cancel calls API + refreshes all', async () => {
    const updated = [{ decision_id: 'd1', status: 'cancelled' }]
    vi.mocked(api.cancelDecision).mockResolvedValue({ decision_id: 'd1' })
    vi.mocked(api.fetchAllDecisions)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(updated)
    const wrapper = mountStore()
    await flushPromises()
    await (wrapper.vm as unknown as {
      cancel: (id: string, reason: string) => Promise<void>
    }).cancel('d1', 'cancel reason')
    await flushPromises()
    expect(api.cancelDecision).toHaveBeenCalledWith('d1', 'cancel reason')
    const s = wrapper.vm as unknown as { all: Array<{ status: string }> }
    expect(s.all[0].status).toBe('cancelled')
  })

  test('lastError set on fetch failure (refresh)', async () => {
    vi.mocked(api.fetchAllDecisions).mockRejectedValue(new Error('network down'))
    const wrapper = mountStore()
    await flushPromises()
    const s = wrapper.vm as unknown as {
      lastError: string | null; loading: boolean
    }
    expect(s.lastError).toContain('network down')
    expect(s.loading).toBe(false)
  })
})
