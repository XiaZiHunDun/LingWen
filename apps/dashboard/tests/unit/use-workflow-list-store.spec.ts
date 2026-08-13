// tests/unit/use-workflow-list-store.spec.ts — Phase 8.34
// useWorkflowListStore module-level singleton test
// 镜像 useDecisionStore 测试隔离模式:
//   vi.mock(...) at top, vi.resetModules() + dynamic import per test
//   to avoid state contamination between tests.
import { beforeEach, describe, expect, test, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'

// Phase 8.34: useWorkflowListStore module-level singleton
// Simpler than useDecisionStore — only owns workflows list + refresh action.
// Per-page UI state (selected, initialInputsJson, maxBacktracks, running,
// showGraph, graphData, graphLoading, active) stays in WorkflowsPage.
vi.mock('../../src/api/index.js', () => ({
  fetchWorkflows: vi.fn(),
}))

let useWorkflowListStore: typeof import('../../src/composables/useWorkflowListStore.js').useWorkflowListStore
let api: typeof import('../../src/api/index.js')

beforeEach(async () => {
  vi.resetModules()
  api = await import('../../src/api/index.js')
  vi.mocked(api.fetchWorkflows).mockReset()
  vi.mocked(api.fetchWorkflows).mockResolvedValue([])
  const mod = await import('../../src/composables/useWorkflowListStore.js')
  useWorkflowListStore = mod.useWorkflowListStore
})

function mountStore() {
  const Harness = defineComponent({
    setup() {
      return useWorkflowListStore()
    },
    render() { return h('div') },
  })
  return mount(Harness)
}

describe('useWorkflowListStore — Phase 8.34 module-level singleton', () => {
  test('initial state: workflows=[], loading=false, lastError=null', () => {
    const wrapper = mountStore()
    const s = wrapper.vm as unknown as {
      workflows: unknown[]; loading: boolean; lastError: string | null
    }
    expect(s.workflows).toEqual([])
    expect(s.loading).toBe(false)
    expect(s.lastError).toBeNull()
  })

  test('refresh populates workflows from fetchWorkflows', async () => {
    vi.mocked(api.fetchWorkflows).mockResolvedValue([
      { id: 'w1', name: 'novel_writing' },
      { id: 'w2', name: 'character_design' },
    ])
    const wrapper = mountStore()
    await flushPromises()
    const s = wrapper.vm as unknown as {
      workflows: Array<{ id: string; name: string }>
    }
    expect(api.fetchWorkflows).toHaveBeenCalledTimes(1)
    expect(s.workflows.length).toBe(2)
    expect(s.workflows[0].name).toBe('novel_writing')
  })

  test('lastError set on fetch failure (refresh)', async () => {
    vi.mocked(api.fetchWorkflows).mockRejectedValue(new Error('500 internal'))
    const wrapper = mountStore()
    await flushPromises()
    const s = wrapper.vm as unknown as {
      lastError: string | null; loading: boolean
    }
    expect(s.lastError).toContain('500 internal')
    expect(s.loading).toBe(false)
  })
})
