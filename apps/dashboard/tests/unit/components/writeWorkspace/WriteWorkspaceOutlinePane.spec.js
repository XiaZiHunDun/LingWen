import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceOutlinePane from '@/components/writeWorkspace/WriteWorkspaceOutlinePane.vue'

describe('WriteWorkspaceOutlinePane', () => {
  const scenes = [
    { id: 's1', title: '雨夜', wordCount: 412 },
    { id: 's2', title: '剑光', wordCount: 387 },
  ]

  it('renders one card per scene', () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's1' } })
    expect(wrapper.findAll('[data-testid="scene-card"]')).toHaveLength(2)
  })

  it('highlights active scene', () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's2' } })
    const cards = wrapper.findAll('[data-testid="scene-card"]')
    expect(cards[1].classes()).toContain('is-active')
  })

  it('emits select-scene when card clicked', async () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's1' } })
    await wrapper.findAll('[data-testid="scene-card"]')[1].trigger('click')
    expect(wrapper.emitted('selectScene')).toBeTruthy()
    expect(wrapper.emitted('selectScene')[0]).toEqual(['s2'])
  })

  it('shows total word count', () => {
    const wrapper = mount(WriteWorkspaceOutlinePane, { props: { scenes, activeSceneId: 's1' } })
    expect(wrapper.text()).toContain('799')
  })
})
