// tests/unit/ripples-page-smoke.spec.ts — Phase 9.31 F15
// 替代 tests/e2e-smoke/ripples.spec.js (3 tests)

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  fetchRipples: vi.fn(),
  fetchRippleStats: vi.fn(),
  fetchRippleDetail: vi.fn(),
  fetchReferenceGraph: vi.fn(),
  applyRipple: vi.fn().mockResolvedValue({ ripple_id: 'rip-1', status: 'applied' }),
}))

vi.mock('../../src/api/index.js', () => ({
  fetchRipples: mocks.fetchRipples,
  fetchRippleStats: mocks.fetchRippleStats,
  fetchRippleDetail: mocks.fetchRippleDetail,
  fetchReferenceGraph: mocks.fetchReferenceGraph,
  fetchRippleAudit: vi.fn().mockResolvedValue([]),
  applyRipple: vi.fn().mockResolvedValue({ ripple_id: 'rip-1', status: 'applied' }),
  rejectRipple: vi.fn().mockResolvedValue({ ripple_id: 'rip-1', status: 'rejected' }),
  rollbackRipple: vi.fn(),
  fetchRippleCascade: vi.fn().mockResolvedValue({ cascade_nodes: [], cascade_edges: [] }),
  fetchRipplePreview: vi.fn().mockResolvedValue({ affected_chapter_count: 0 }),
}))

vi.mock('../../src/composables/useRippleSocket.js', () => ({
  useRippleSocket: () => ({
    pendingUpdates: { value: [] },
    connect: vi.fn(),
  }),
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: { value: null },
    pendingDecisions: { value: [] },
    connected: { value: true },
    lastError: { value: null },
    sendKeepAlive: vi.fn(),
    reconnect: vi.fn(),
  }),
  onCascadeUpdate: vi.fn(),
  onAuditCreated: vi.fn(() => () => {}),
}))

const sampleRipple = {
  ripple_id: 'rip-1',
  dimension: 'character',
  relationship_type: 'causes',
  source_chapter: 5,
  target_chapter: 10,
  status: 'pending',
  confidence: 4,
  created_at: '2026-06-10T12:00:00Z',
  evidence: 'mock',
  source_payload: {},
  target_payload: {},
  edge_payload: {},
}

import RipplesPage from '../../src/pages/RipplesPage.vue'

describe('RipplesPage smoke (Phase 9.31 F15)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.fetchRipples.mockResolvedValue([sampleRipple])
    mocks.fetchRippleStats.mockResolvedValue({ total: 1, by_status: { pending: 1 }, by_volume: { 1: 1 } })
    mocks.fetchRippleDetail.mockResolvedValue(sampleRipple)
    mocks.fetchReferenceGraph.mockResolvedValue({
      nodes: [],
      edges: [],
      total_node_count: 0,
      total_edge_count: 0,
      truncated: false,
    })
  })

  test('mount renders impact graph section + filter + ripple list', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    expect(wrapper.find(byTestid('ripples-page-impact-graph')).exists()).toBe(true)
    expect(wrapper.find(byTestid('ripple-filter-status')).exists()).toBe(true)
    expect(wrapper.find(byTestid('ripple-card')).exists()).toBe(true)
    expect(mocks.fetchReferenceGraph).toHaveBeenCalled()
  })

  test('pending filter shows list or empty/loading state', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    const statusSelect = wrapper.find(byTestid('ripple-filter-status'))
    await statusSelect.setValue('pending')
    await flushPromises()
    const hasCard = wrapper.find(byTestid('ripple-card')).exists()
    const hasEmpty = wrapper.find(byTestid('ripple-list-empty')).exists()
    const hasLoading = wrapper.find(byTestid('ripple-list-loading')).exists()
    expect(hasCard || hasEmpty || hasLoading).toBe(true)
  })

  test('open drawer then close hides drawer content', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    await wrapper.find(byTestid('ripple-card')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('ripple-drawer')).exists()).toBe(true)
    await wrapper.find(byTestid('ripple-drawer-close')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('ripple-drawer-content')).exists()).toBe(false)
  })

  test('impact score sort filter triggers fetch with sort_by', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    await wrapper.find(byTestid('ripple-filter-sort')).setValue('impact_score')
    await flushPromises()
    const lastCall = mocks.fetchRipples.mock.calls.at(-1)?.[0] as URLSearchParams
    expect(lastCall.toString()).toContain('sort_by=impact_score')
  })
})
