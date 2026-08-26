import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceAIDrawer from '@/components/writeWorkspace/WriteWorkspaceAIDrawer.vue'

describe('WriteWorkspaceAIDrawer', () => {
  const context = {
    current_chapter_heading: '灰烬中的回声',
    current_scene: '雨夜',
    current_scene_body: '雨下得很大。',
    prev_chapter_tail: '',
    characters_in_scene: ['林夜', '莫言'],
  }

  it('renders context header when open', () => {
    const wrapper = mount(WriteWorkspaceAIDrawer, {
      props: { open: true, context },
      global: { stubs: {} },
    })
    expect(wrapper.text()).toContain('灰烬中的回声')
    expect(wrapper.text()).toContain('雨夜')
  })

  it('hides when open=false', () => {
    const wrapper = mount(WriteWorkspaceAIDrawer, {
      props: { open: false, context },
      global: { stubs: {} },
    })
    expect(wrapper.find('[data-testid="ai-drawer"]').classes()).toContain('is-closed')
  })

  it('emits close when X clicked', async () => {
    const wrapper = mount(WriteWorkspaceAIDrawer, {
      props: { open: true, context },
      global: { stubs: {} },
    })
    await wrapper.find('[data-testid="close-btn"]').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})