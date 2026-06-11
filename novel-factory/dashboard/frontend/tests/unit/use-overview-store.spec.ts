// tests/unit/use-overview-store.spec.ts — Phase 8.34
// useOverviewStore module-level singleton test
// 镜像 useWorkflowListStore 测试隔离模式 (single fetch + lastError):
//   vi.mock(...) at top, vi.resetModules() + dynamic import per test
//   to avoid state contamination between tests.
// 区别 (over useWorkflowListStore): store owns 2 refs (overview + chapters),
//   refresh 用 Promise.all 并行 fetch. loading 翻转两次 (true → false),
//   任一 fetch 失败 lastError 都被设.
import { beforeEach, describe, expect, test, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'

// Phase 8.34: useOverviewStore module-level singleton
// Owns overview + chapters data, fetched in parallel via Promise.all.
// Per-page UI state (chartData, statCards computed) stays in OverviewPage.
vi.mock('../../src/api/index.js', () => ({
  fetchOverview: vi.fn(),
  fetchChapters: vi.fn(),
}))

let useOverviewStore: typeof import('../../src/composables/useOverviewStore.js').useOverviewStore
let api: typeof import('../../src/api/index.js')

beforeEach(async () => {
  vi.resetModules()
  api = await import('../../src/api/index.js')
  vi.mocked(api.fetchOverview).mockReset()
  vi.mocked(api.fetchChapters).mockReset()
  vi.mocked(api.fetchOverview).mockResolvedValue({})
  vi.mocked(api.fetchChapters).mockResolvedValue([])
  const mod = await import('../../src/composables/useOverviewStore.js')
  useOverviewStore = mod.useOverviewStore
})

function mountStore() {
  const Harness = defineComponent({
    setup() {
      return useOverviewStore()
    },
    render() { return h('div') },
  })
  return mount(Harness)
}

describe('useOverviewStore — Phase 8.34 module-level singleton', () => {
  test('initial state: overview={}, chapters=[], loading=false, lastError=null', () => {
    const wrapper = mountStore()
    const s = wrapper.vm as unknown as {
      overview: Record<string, unknown>; chapters: unknown[]
      loading: boolean; lastError: string | null
    }
    expect(s.overview).toEqual({})
    expect(s.chapters).toEqual([])
    expect(s.loading).toBe(false)
    expect(s.lastError).toBeNull()
  })

  test('refresh fetches overview + chapters in parallel via Promise.all', async () => {
    vi.mocked(api.fetchOverview).mockResolvedValue({ total_chapters: 359, total_words: 1234567 })
    // fetchChapters 实际返回 envelope { chapters: [...] } (mirror OverviewPage 原 L110)
    vi.mocked(api.fetchChapters).mockResolvedValue({
      chapters: [
        { chapter_num: 1, title: 'ch1' },
        { chapter_num: 2, title: 'ch2' },
      ],
    })
    const wrapper = mountStore()
    await flushPromises()
    const s = wrapper.vm as unknown as {
      overview: { total_chapters: number }
      chapters: Array<{ chapter_num: number }>
    }
    expect(api.fetchOverview).toHaveBeenCalledTimes(1)
    expect(api.fetchChapters).toHaveBeenCalledTimes(1)
    expect(s.overview.total_chapters).toBe(359)
    expect(s.chapters.length).toBe(2)
  })

  test('lastError set on fetch failure (refresh)', async () => {
    vi.mocked(api.fetchOverview).mockRejectedValue(new Error('overview 503'))
    const wrapper = mountStore()
    await flushPromises()
    const s = wrapper.vm as unknown as {
      lastError: string | null; loading: boolean
    }
    expect(s.lastError).toContain('overview 503')
    expect(s.loading).toBe(false)
  })
})
