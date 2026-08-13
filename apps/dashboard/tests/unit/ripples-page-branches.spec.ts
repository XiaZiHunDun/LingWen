// tests/unit/ripples-page-branches.spec.ts — Phase 9.57 F48
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { byTestid } from '../helpers/by-testid'

const pendingUpdates = ref<Array<Record<string, unknown>>>([])

const mocks = vi.hoisted(() => ({
  fetchRipples: vi.fn(),
  fetchRippleStats: vi.fn(),
  fetchRippleDetail: vi.fn(),
  fetchReferenceGraph: vi.fn(),
  applyRipple: vi.fn(),
  rejectRipple: vi.fn(),
}))

vi.mock('../../src/api/index.js', () => ({
  fetchRipples: mocks.fetchRipples,
  fetchRippleStats: mocks.fetchRippleStats,
  fetchRippleDetail: mocks.fetchRippleDetail,
  fetchReferenceGraph: mocks.fetchReferenceGraph,
  fetchRippleAudit: vi.fn().mockResolvedValue([]),
  applyRipple: mocks.applyRipple,
  rejectRipple: mocks.rejectRipple,
  rollbackRipple: vi.fn(),
  fetchRippleCascade: vi.fn().mockResolvedValue({ cascade_nodes: [], cascade_edges: [] }),
  fetchRipplePreview: vi.fn().mockResolvedValue({}),
}))

vi.mock('../../src/composables/useRippleSocket.js', () => ({
  useRippleSocket: () => ({
    pendingUpdates,
    connect: vi.fn(),
  }),
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
  impact_score: 10,
}

import RipplesPage from '../../src/pages/RipplesPage.vue'

describe('RipplesPage branches (F48)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    pendingUpdates.value = []
    mocks.fetchRipples.mockResolvedValue([sampleRipple])
    mocks.fetchRippleStats.mockResolvedValue({ total: 1, by_status: { pending: 1 }, by_volume: { 1: 1 } })
    mocks.fetchRippleDetail.mockResolvedValue({ ...sampleRipple, evidence: '' })
    mocks.fetchReferenceGraph.mockResolvedValue({
      nodes: [{ id: 'n1', dimension: 'character', volume: 1, chapter: 1, title: 'A' }],
      edges: [],
      total_node_count: 1,
      total_edge_count: 0,
      truncated: false,
    })
    mocks.applyRipple.mockResolvedValue({ ripple_id: 'rip-1', status: 'applied' })
    mocks.rejectRipple.mockResolvedValue({ ripple_id: 'rip-1', status: 'rejected' })
  })

  test('reference graph fetch error uses empty fallback', async () => {
    mocks.fetchReferenceGraph.mockRejectedValueOnce(new Error('fail'))
    const wrapper = mount(RipplesPage)
    await flushPromises()
    expect(wrapper.find(byTestid('impact-graph-empty')).exists()).toBe(true)
  })

  test('volume and dimension filters passed to fetchReferenceGraph', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    await wrapper.find(byTestid('ripple-filter-volume')).setValue('2')
    await wrapper.find(byTestid('ripple-filter-dimension')).setValue('character')
    await flushPromises()
    const lastUrl = mocks.fetchReferenceGraph.mock.calls.at(-1)?.[0]
    expect(lastUrl).toMatchObject({ volume: 2, dimension: 'character' })
  })

  test('min_score filter triggers refresh params', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    await wrapper.find(byTestid('ripple-filter-min-score')).setValue('5')
    await flushPromises()
    const params = mocks.fetchRipples.mock.calls.at(-1)?.[0] as URLSearchParams
    expect(params.toString()).toContain('min_score=5')
  })

  test('apply and reject from drawer emitters', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    await wrapper.find(byTestid('ripple-card')).trigger('click')
    await flushPromises()
    const drawer = wrapper.findComponent({ name: 'RippleDrawer' })
    await drawer.vm.$emit('apply')
    await flushPromises()
    expect(mocks.applyRipple).toHaveBeenCalledWith('rip-1')
    await drawer.vm.$emit('reject')
    await flushPromises()
    expect(mocks.rejectRipple).toHaveBeenCalled()
  })

  test('impact graph node-click no-op', async () => {
    const wrapper = mount(RipplesPage)
    await flushPromises()
    const graph = wrapper.findComponent({ name: 'ImpactGraph' })
    await graph.vm.$emit('nodeClick', { nodeId: 'n1' })
  })
})
