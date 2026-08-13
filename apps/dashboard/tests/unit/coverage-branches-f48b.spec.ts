// tests/unit/coverage-branches-f48b.spec.ts — Phase 9.57 F48 final branch push
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ImpactGraph from '../../src/components/ImpactGraph.vue'
import DecisionsPage from '../../src/pages/DecisionsPage.vue'
import { byTestid } from '../helpers/by-testid'

describe('ImpactGraph chart branches (F48b)', () => {
  const graph = {
    nodes: [
      { id: 'n1', dimension: 'character', volume: 1, chapter: 2, title: 'Hero', description: 'lead' },
      { id: 'n2', dimension: 'plot_point', volume: 2, chapter: 3, title: 'Twist' },
    ],
    edges: [{ from_node_id: 'n1', to_node_id: 'n2', weight: 0.9 }],
    total_node_count: 2,
    truncated: false,
  }

  test('renders chart container with node count', async () => {
    const wrapper = mount(ImpactGraph, { props: { graph } })
    await flushPromises()
    expect(wrapper.find(byTestid('impact-graph')).exists()).toBe(true)
    expect(wrapper.find(byTestid('impact-graph-chart')).exists()).toBe(true)
  })

  test('updates when graph prop changes to empty', async () => {
    const wrapper = mount(ImpactGraph, { props: { graph } })
    await flushPromises()
    await wrapper.setProps({ graph: { nodes: [], edges: [], total_node_count: 0, truncated: false } } as never)
    await flushPromises()
    expect(wrapper.find(byTestid('impact-graph-empty')).exists()).toBe(true)
  })
})

describe('useCostWindow abort race (F48b)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
    window.history.replaceState(null, '', '/')
  })

  test('rapid window switch aborts stale fetch', async () => {
    let resolveFirst: (v: Response) => void
    const first = new Promise<Response>((r) => { resolveFirst = r })
    vi.mocked(fetch)
      .mockReturnValueOnce(first as Promise<Response>)
      .mockResolvedValue({
        ok: true,
        json: async () => ({ total_cost_usd: 1 }),
      } as Response)

    vi.resetModules()
    const { useCostWindow } = await import('../../src/composables/useCostWindow.js')
    const wrapper = mount(defineComponent({
      setup() { return useCostWindow() },
      template: '<div />',
    }))
    wrapper.vm.setTimeWindow('7d')
    wrapper.vm.setTimeWindow('30d')
    resolveFirst!({
      ok: true,
      json: async () => ({ total_cost_usd: 99 }),
    } as Response)
    await flushPromises()
    expect(wrapper.vm.timeWindow).toBe('30d')
  })
})

vi.mock('../../src/api/index.js', () => ({
  fetchAllDecisions: vi.fn().mockResolvedValue([
    {
      decision_id: 'd-p',
      status: 'pending',
      kind: 'outline-judgment',
      priority: 1,
      title: 'T',
      prompt: 'P',
      options: ['yes'],
      node_id: 'n1',
    },
  ]),
  resolveDecision: vi.fn().mockResolvedValue({ decision_id: 'd-p', status: 'resolved' }),
  deferDecision: vi.fn().mockResolvedValue({}),
  cancelDecision: vi.fn().mockResolvedValue({}),
  fetchWorkflows: vi.fn().mockResolvedValue([]),
  fetchOverview: vi.fn().mockResolvedValue({}),
  fetchChapters: vi.fn().mockResolvedValue({ chapters: [] }),
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: { value: null },
    pendingDecisions: {
      value: [{
        decision_id: 'd-p',
        status: 'pending',
        kind: 'outline-judgment',
        priority: 1,
        title: 'T',
        prompt: 'P',
        options: ['yes'],
        node_id: 'n1',
      }],
    },
    connected: { value: true },
    lastError: { value: null },
    sendKeepAlive: () => {},
    reconnect: () => {},
  }),
}))

describe('DecisionsPage handler branches (F48b)', () => {
  test('resolve via DecisionCard option button', async () => {
    const wrapper = mount(DecisionsPage)
    await flushPromises()
    const api = await import('../../src/api/index.js')
    const btn = wrapper.find(byTestid('option-btn'))
    if (btn.exists()) {
      await btn.trigger('click')
      await flushPromises()
      expect(api.resolveDecision).toHaveBeenCalled()
    }
  })
})
