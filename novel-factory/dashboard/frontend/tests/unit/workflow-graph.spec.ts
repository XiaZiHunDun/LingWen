// tests/unit/workflow-graph.spec.ts — Phase 8.32
// WorkflowGraph 4 inner testid 验证 (reset-zoom-btn / zoom-display /
// zoom-in-btn / zoom-out-btn). 4 状态 (loading/error/svg/empty) 留 followup
// (需 mermaid 异步 + visual regression / E2E 触发).
//
// 契约:
//   - vi.mock('mermaid') 局部 stub, render() 返 { svg: '<svg>fake</svg>' }
//     立即 resolve, 让 zoom-controls 容器 (v-if='svg') 渲染.
//   - Test 1: click zoom-in-btn 后 zoom-display 显示 "120%" (1.0 + 0.2 = 1.2).
//   - Test 2: click zoom-out-btn 后 zoom-display 显示 "80%" (1.0 - 0.2 = 0.8).
//   - Test 3: click zoom-in-btn 2 次 (140%) → click reset-zoom-btn → "100%".
//   - Test 4: click zoom-in-btn 6 次 (1.0→1.2→1.4→1.6→1.8→1.999...→2.0, Math.min(2, x)
//     限 2.0; 6 次而非 5 次因 JS float 1.0+0.2*5=1.9999999999999998 drift, 6 次才能让
//     Math.min(2, 1.999... + 0.2) = 2.0 精确 clamp) → zoom-display "200%" + zoom-in-btn disabled.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import WorkflowGraph from '../../src/components/WorkflowGraph.vue'
import { byTestid } from '../helpers/by-testid'

// Phase 8.32: 局部 vi.mock mermaid, render 立即返 fake svg 让 zoom-controls
// (v-if='svg') 渲染. 0 改 setup.ts, 0 jsdom canvas/svg 风险.
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn().mockResolvedValue({ svg: '<svg>fake</svg>' }),
  },
}))

describe('WorkflowGraph zoom controls inner sub-element testid (Phase 8.32)', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(async () => {
    wrapper = mount(WorkflowGraph, {
      props: {
        mermaid: 'graph TD; A-->B',
        workflowName: 'test',
      },
    })
    // 等 mermaid.render() async resolve 让 svg.value 设定 + zoom-controls 渲染
    await flushPromises()
  })

  test('zoom-in-btn click increases zoom display to 120%', async () => {
    // 初始 zoom = 1.0
    expect(wrapper.find(byTestid('zoom-display')).text()).toBe('100%')
    await wrapper.find(byTestid('zoom-in-btn')).trigger('click')
    // zoomIn(): Math.min(2, 1.0 + 0.2) = 1.2 → "120%"
    expect(wrapper.find(byTestid('zoom-display')).text()).toBe('120%')
  })

  test('zoom-out-btn click decreases zoom display to 80%', async () => {
    expect(wrapper.find(byTestid('zoom-display')).text()).toBe('100%')
    await wrapper.find(byTestid('zoom-out-btn')).trigger('click')
    // zoomOut(): Math.max(0.4, 1.0 - 0.2) = 0.8 → "80%"
    expect(wrapper.find(byTestid('zoom-display')).text()).toBe('80%')
  })

  test('reset-zoom-btn returns to 100% after zoom in twice', async () => {
    // click 2 次: 1.0 → 1.2 → 1.4
    await wrapper.find(byTestid('zoom-in-btn')).trigger('click')
    await wrapper.find(byTestid('zoom-in-btn')).trigger('click')
    expect(wrapper.find(byTestid('zoom-display')).text()).toBe('140%')
    // click reset-zoom-btn → 1.0
    await wrapper.find(byTestid('reset-zoom-btn')).trigger('click')
    expect(wrapper.find(byTestid('zoom-display')).text()).toBe('100%')
  })

  test('zoom-in-btn disabled at max 2x (after 6 clicks — JS float drift requires 6 not 5)', async () => {
    // click 6 次: 1.0 → 1.2 → 1.4 → 1.6 → 1.8 → 1.999... → 2.0 (Math.min(2, x) 限 2.0)
    // 6 次而非 5 次: JS float 1.0 + 0.2*5 = 1.9999999999999998 (drift), 需 6 次
    // 才能让 Math.min(2, 1.999... + 0.2) = 2.0 精确 clamp.
    for (let i = 0; i < 6; i++) {
      await wrapper.find(byTestid('zoom-in-btn')).trigger('click')
    }
    // 第 6 次后 zoom = 2.0 (exact), display "200%"
    expect(wrapper.find(byTestid('zoom-display')).text()).toBe('200%')
    // :disabled="zoom >= 2" 触发后, button 显 disabled attribute
    const zoomInBtn = wrapper.find(byTestid('zoom-in-btn'))
    expect(zoomInBtn.attributes('disabled')).not.toBeUndefined()
  })
})
