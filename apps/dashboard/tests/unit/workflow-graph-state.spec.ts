// tests/unit/workflow-graph-state.spec.ts — Phase 9.52 F41
// WorkflowGraph 4 UI state testid: loading / error / graph / empty

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import WorkflowGraph from '../../src/components/WorkflowGraph.vue'
import { byTestid } from '../helpers/by-testid'

const fakeMermaidResult = { svg: '<svg>fake</svg>', diagramType: 'flowchart-v2' as const }

vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(),
  },
}))

describe('WorkflowGraph 4 UI state testid (Phase 9.52 F41)', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    const mermaid = await import('mermaid')
    vi.mocked(mermaid.default.render).mockResolvedValue(fakeMermaidResult)
  })

  test('workflow-graph-loading visible while mermaid render is pending', async () => {
    const mermaid = await import('mermaid')
    vi.mocked(mermaid.default.render).mockImplementationOnce(
      () => new Promise(() => {}),
    )

    const wrapper = mount(WorkflowGraph, {
      props: { mermaid: 'graph TD; A-->B', workflowName: 'test' },
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.find(byTestid('workflow-graph-loading')).exists()).toBe(true)
  })

  test('workflow-graph-error visible when mermaid render fails', async () => {
    const mermaid = await import('mermaid')
    vi.mocked(mermaid.default.render).mockRejectedValueOnce(new Error('bad syntax'))

    const wrapper = mount(WorkflowGraph, {
      props: { mermaid: 'graph TD; BAD', workflowName: 'test' },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('workflow-graph-error')).exists()).toBe(true)
    expect(wrapper.text()).toContain('bad syntax')
  })

  test('workflow-graph-graph visible after successful render', async () => {
    const wrapper = mount(WorkflowGraph, {
      props: { mermaid: 'graph TD; A-->B', workflowName: 'test' },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('workflow-graph-graph')).exists()).toBe(true)
    expect(wrapper.find(byTestid('workflow-graph-loading')).exists()).toBe(false)
  })

  test('workflow-graph-empty visible when mermaid string is empty', async () => {
    const wrapper = mount(WorkflowGraph, {
      props: { mermaid: '', workflowName: 'test' },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('workflow-graph-empty')).exists()).toBe(true)
    expect(wrapper.find(byTestid('workflow-graph-graph')).exists()).toBe(false)
  })
})
