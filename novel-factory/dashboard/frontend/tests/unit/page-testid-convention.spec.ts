// tests/unit/page-testid-convention.spec.ts — Phase 9.30 F14
// DecisionsPage / WorkflowsPage page-level testid 跟 OverviewPage 对齐 (0 class selector in spec)

import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

vi.mock('../../src/api/index.js', () => ({
  fetchAllDecisions: vi.fn().mockResolvedValue([]),
  resolveDecision: vi.fn().mockResolvedValue({}),
  deferDecision: vi.fn().mockResolvedValue({}),
  cancelDecision: vi.fn().mockResolvedValue({}),
  fetchWorkflows: vi.fn().mockResolvedValue([
    { name: 'novel_writing', node_count: 7, path: 'wf/novel_writing.yaml', has_decision_nodes: true },
  ]),
  fetchOverview: vi.fn().mockResolvedValue({}),
  fetchChapters: vi.fn().mockResolvedValue({ chapters: [] }),
  fetchWorkflowGraph: vi.fn().mockResolvedValue({ mermaid: 'graph TD\n  A-->B', workflow_name: 'novel_writing' }),
  runWorkflow: vi.fn().mockResolvedValue({ workflow_name: 'novel_writing', is_active: true }),
  resumeWorkflow: vi.fn().mockResolvedValue({ workflow_name: 'novel_writing', is_active: true }),
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: { value: null },
    pendingDecisions: { value: [] },
    connected: { value: true },
    lastError: { value: null },
    sendKeepAlive: () => {},
    reconnect: () => {},
  }),
}))

import DecisionsPage from '../../src/pages/DecisionsPage.vue'
import WorkflowsPage from '../../src/pages/WorkflowsPage.vue'

describe('Page testid convention (Phase 9.30 F14)', () => {
  test('DecisionsPage exposes refresh-btn + count-badge testids', async () => {
    const wrapper = mount(DecisionsPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).exists()).toBe(true)
    expect(wrapper.find(byTestid('refresh-btn')).exists()).toBe(true)
    expect(wrapper.find(byTestid('count-badge')).exists()).toBe(true)
  })

  test('WorkflowsPage exposes refresh-btn + wf-item testids', async () => {
    const wrapper = mount(WorkflowsPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).exists()).toBe(true)
    expect(wrapper.find(byTestid('refresh-btn')).exists()).toBe(true)
    expect(wrapper.findAll(byTestid('wf-item')).length).toBeGreaterThan(0)
  })
})
