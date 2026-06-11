// tests/unit/chapters-page.spec.ts — Phase 9.71 F63
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChaptersPage from '../../src/pages/ChaptersPage.vue'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  fetchChapters: vi.fn(),
  fetchProductionRecords: vi.fn(),
  fetchProductionRollup: vi.fn(),
  pendingDecisions: { value: [] as Array<Record<string, unknown>> },
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
  fetchProductionRecords: mocks.fetchProductionRecords,
  fetchProductionRollup: mocks.fetchProductionRollup,
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: mocks.status,
    pendingDecisions: mocks.pendingDecisions,
    connected: { value: true },
    lastError: { value: null },
  }),
}))

const navMocks = vi.hoisted(() => ({
  navigateTo: vi.fn(),
}))

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    navigateTo: navMocks.navigateTo,
  }),
}))

describe('ChaptersPage (F63/F88)', () => {
  beforeEach(() => {
    mocks.fetchProductionRecords.mockResolvedValue({ records: [] })
    mocks.fetchProductionRollup.mockResolvedValue({ batches: [] })
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
    mocks.pendingDecisions.value = []
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

  test('shows latest batch badge from rollup', async () => {
    mocks.fetchProductionRollup.mockResolvedValue({
      batch_count: 1,
      batches: [{
        record_id: 'batch-361-363',
        chapter_range: '361-363',
        total_cost_usd: 0.083,
        stopped_reason: 'completed',
        recorded_at: '2026-06-11T01:00:00Z',
      }],
    })
    const wrapper = mount(ChaptersPage)
    await flushPromises()
    const badge = wrapper.find(byTestid('latest-batch-badge'))
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toContain('ch361-363')
    expect(badge.text()).toContain('completed')
  })

  test('shows production history table when records present', async () => {
    mocks.fetchProductionRecords.mockResolvedValue({
      records: [
        {
          record_id: 'p360',
          record_type: 'pilot',
          chapter_num: 360,
          chapter_range: null,
          operator: 'op',
          recorded_at: '2026-06-11T00:00:00Z',
          provider: 'minimax',
          total_cost_usd: 0.025,
          emit_chapter_completed: true,
          memory_context_source: 'stub',
          stopped_reason: null,
          source_file: 'ch360.json',
        },
      ],
    })
    const wrapper = mount(ChaptersPage)
    await flushPromises()
    expect(wrapper.find(byTestid('production-history-table')).exists()).toBe(true)
    expect(wrapper.text()).toContain('minimax')
    expect(wrapper.text()).toContain('#360')
  })

  test('chapter decision link navigates to decisions', async () => {
    mocks.fetchChapters.mockResolvedValue({
      chapters: [{ chapter: 5, hook_count: 1, hook_strength_avg: 0.5, coolpoint_count: 0, coolpoint_density: 0.1 }],
    })
    mocks.pendingDecisions.value = [
      { decision_id: 'd5', status: 'pending', context: { chapter_num: 5 } },
    ]
    mocks.status.value = { is_active: true, paused: true, production_summary: { chapter_num: 5 } }
    const wrapper = mount(ChaptersPage)
    await flushPromises()
    const link = wrapper.find('[data-testid="chapter-decision-link"]')
    expect(link.exists()).toBe(true)
    await link.trigger('click')
    expect(navMocks.navigateTo).toHaveBeenCalledWith('decisions', {
      chapter: 5,
      decisionId: 'd5',
    })
  })
})
