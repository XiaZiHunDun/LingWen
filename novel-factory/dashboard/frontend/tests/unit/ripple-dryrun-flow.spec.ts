// tests/unit/ripple-dryrun-flow.spec.ts — Phase 9.31 F15
// 替代 tests/e2e-smoke/ripple-dryrun.spec.js (3 tests)

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

const dryRunMocks = vi.hoisted(() => ({
  cascade: {
    trigger_ripple_id: 'rip-1',
    cascade_nodes: [
      { id: 'n-trigger', dimension: 'character', volume: 1, chapter: 5, title: 'trigger', description: '', payload: {} },
      { id: 'n-down', dimension: 'character', volume: 1, chapter: 10, title: 'downstream', description: '', payload: {} },
    ],
    cascade_edges: [],
    cascade_actions: [],
    depth_reached: 1,
    generated_at: '2026-06-10T12:00:00+00:00',
    bfs_algorithm_version: 'v1',
  },
  preview: {
    ripple_id: 'rip-1',
    affected_chapter_count: 1,
    affected_character_count: 1,
    affected_setting_count: 0,
    estimated_change_count: 1,
    cascade_node_count: 2,
    cascade_edge_count: 1,
    max_depth: 1,
  },
}))

vi.mock('echarts/core', () => ({
  default: {
    init: vi.fn(() => ({ setOption: vi.fn(), on: vi.fn(), resize: vi.fn(), dispose: vi.fn() })),
  },
  init: vi.fn(() => ({ setOption: vi.fn(), on: vi.fn(), resize: vi.fn(), dispose: vi.fn() })),
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

vi.mock('../../src/api/index.js', () => ({
  fetchRippleAudit: vi.fn().mockResolvedValue([]),
  rollbackRipple: vi.fn(),
  fetchRipples: vi.fn().mockResolvedValue([]),
  fetchRippleStats: vi.fn().mockResolvedValue({ total: 0, by_status: {}, by_volume: {} }),
  applyRipple: vi.fn(),
  rejectRipple: vi.fn(),
  fetchRippleCascade: vi.fn().mockResolvedValue(dryRunMocks.cascade),
  fetchRipplePreview: vi.fn().mockResolvedValue(dryRunMocks.preview),
  fetchCascadeRuns: vi.fn().mockResolvedValue([]),
  fetchCascadeRunReplay: vi.fn(),
  cancelCascadeRun: vi.fn(),
}))

import RippleDrawer from '../../src/components/RippleDrawer.vue'

const baseRipple = {
  ripple_id: 'rip-1',
  dimension: 'character',
  relationship_type: 'causes',
  source_chapter: 5,
  target_chapter: 10,
  status: 'pending',
  confidence: 4,
  evidence: 'mock evidence',
  source_payload: {},
  target_payload: {},
  edge_payload: {},
  created_at: '2026-06-10T12:00:00Z',
}

async function mountDrawerOpen() {
  const wrapper = mount(RippleDrawer, { props: { ripple: baseRipple, open: true }, attachTo: document.body })
  await flushPromises()
  await wrapper.find(byTestid('tab-cascade')).trigger('click')
  await flushPromises()
  return wrapper
}

describe('Ripple dry-run flow (Phase 9.31 F15)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('dry-run toggle shows summary chips and cascade graph', async () => {
    const wrapper = await mountDrawerOpen()
    expect(wrapper.find(byTestid('ripple-dryrun-section')).exists()).toBe(true)
    await wrapper.find(byTestid('dry-run-toggle')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('ripple-summary-chips')).exists()).toBe(true)
    expect(wrapper.find(byTestid('cascade-graph')).exists()).toBe(true)
  })

  test('apply button opens confirmation modal with 4 chip counts', async () => {
    const wrapper = await mountDrawerOpen()
    await wrapper.find(byTestid('ripple-drawer-apply')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('apply-confirm-modal')).exists()).toBe(true)
    expect(wrapper.find(byTestid('apply-confirm-chapter-count')).exists()).toBe(true)
    expect(wrapper.find(byTestid('apply-confirm-character-count')).exists()).toBe(true)
    expect(wrapper.find(byTestid('apply-confirm-setting-count')).exists()).toBe(true)
    expect(wrapper.find(byTestid('apply-confirm-change-count')).exists()).toBe(true)
  })

  test('apply modal cancel closes modal without emitting apply', async () => {
    const wrapper = await mountDrawerOpen()
    await wrapper.find(byTestid('ripple-drawer-apply')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('apply-confirm-modal')).exists()).toBe(true)
    await wrapper.find(byTestid('apply-confirm-cancel')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('apply-confirm-modal')).exists()).toBe(false)
    expect(wrapper.emitted('apply')).toBeFalsy()
    expect(wrapper.find(byTestid('ripple-drawer')).exists()).toBe(true)
  })
})
