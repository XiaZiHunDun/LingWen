import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteInlineAnnotationLayer from '@/components/writeWorkspace/WriteInlineAnnotationLayer.vue'

describe('WriteInlineAnnotationLayer', () => {
  const annotations = [
    { sceneId: 's1', offset: 5, severity: 'P0', rule: 'consistency:character_name', msg: '林夜 vs 林葉 名字冲突' },
    { sceneId: 's1', offset: 20, severity: 'P1', rule: 'pacing:dense', msg: '节奏过密' },
  ]

  it('renders markers for each annotation', () => {
    const wrapper = mount(WriteInlineAnnotationLayer, { props: { annotations } })
    expect(wrapper.findAll('[data-testid="annotation-marker"]')).toHaveLength(2)
  })

  it('shows tooltip on hover', async () => {
    const wrapper = mount(WriteInlineAnnotationLayer, { props: { annotations } })
    await wrapper.findAll('[data-testid="annotation-marker"]')[0].trigger('mouseenter')
    expect(wrapper.text()).toContain('林夜 vs 林葉')
  })

  it('emits jump-to-fix when marker clicked', async () => {
    const wrapper = mount(WriteInlineAnnotationLayer, { props: { annotations } })
    await wrapper.findAll('[data-testid="annotation-marker"]')[0].trigger('click')
    expect(wrapper.emitted('jumpToFix')).toBeTruthy()
    expect(wrapper.emitted('jumpToFix')[0]).toEqual([annotations[0]])
  })
})