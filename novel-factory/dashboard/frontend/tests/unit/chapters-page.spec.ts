// tests/unit/chapters-page.spec.ts — Phase 9.71 F63
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChaptersPage from '../../src/pages/ChaptersPage.vue'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  fetchChapters: vi.fn(),
  status: {
    value: {
      is_active: false,
      workflow_name: null,
      paused: false,
      incremental_backfill: null,
    },
  },
}))

vi.mock('../../src/api/index.js', () => ({
  fetchChapters: mocks.fetchChapters,
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: mocks.status,
    connected: { value: true },
    lastError: { value: null },
  }),
}))

describe('ChaptersPage (F63)', () => {
  beforeEach(() => {
    mocks.fetchChapters.mockResolvedValue({
      chapters: [
        {
          chapter: 1,
          hook_count: 2,
          hook_strength_avg: 0.5,
          coolpoint_count: 1,
          coolpoint_density: 0.1,
        },
      ],
    })
    mocks.status.value = {
      is_active: false,
      workflow_name: null,
      paused: false,
      incremental_backfill: null,
    }
  })

  test('renders page title and chapter table', async () => {
    const wrapper = mount(ChaptersPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('章节管理')
    expect(wrapper.text()).toContain('1')
  })

  test('shows idle production status when no active workflow', async () => {
    const wrapper = mount(ChaptersPage)
    await flushPromises()
    expect(wrapper.find(byTestid('chapter-production-status')).text()).toContain('无活跃工作流')
  })

  test('shows backfill badge when incremental_backfill present', async () => {
    mocks.status.value = {
      is_active: true,
      workflow_name: 'novel_writing',
      paused: false,
      production_summary: {
        chapter_num: 360,
        memory_context_source: 'stub',
        emit_chapter_completed: true,
        incremental_backfill: {
          nodes_written: 2,
          nodes_skipped: 0,
          total_count: 2,
          elapsed_s: 0.1,
        },
      },
      incremental_backfill: {
        nodes_written: 2,
        nodes_skipped: 0,
        total_count: 2,
        elapsed_s: 0.1,
      },
    }
    const wrapper = mount(ChaptersPage)
    await flushPromises()
    expect(wrapper.find(byTestid('chapter-production-summary')).exists()).toBe(true)
    expect(wrapper.text()).toContain('章节 #360')
    expect(wrapper.text()).toContain('Memory: stub')
    expect(wrapper.text()).toContain('写入 2 节点')
  })

  test('reloads when range changes', async () => {
    const wrapper = mount(ChaptersPage)
    await flushPromises()
    expect(mocks.fetchChapters).toHaveBeenCalledWith('1-30')
    await wrapper.find(byTestid('chapter-range-select')).setValue('1-50')
    await flushPromises()
    expect(mocks.fetchChapters).toHaveBeenCalledWith('1-50')
  })
})
