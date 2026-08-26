import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceEditorPane from '@/components/writeWorkspace/WriteWorkspaceEditorPane.vue'

describe('WriteWorkspaceEditorPane', () => {
  it('mounts and shows editor placeholder', () => {
    const wrapper = mount(WriteWorkspaceEditorPane, {
      props: { content: '雨下得很大。', editable: true },
      global: { stubs: { TipTapEditor: true } },
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('[data-testid="editor-pane"]').exists()).toBe(true)
  })

  it('emits update:content when inner editor changes', async () => {
    const wrapper = mount(WriteWorkspaceEditorPane, {
      props: { content: 'initial', editable: true },
      global: { stubs: { TipTapEditor: true } },
    })
    wrapper.vm.handleEditorUpdate('new content')
    expect(wrapper.emitted('update:content')).toBeTruthy()
    expect(wrapper.emitted('update:content')[0]).toEqual(['new content'])
  })

  it('passes editable=false in author mode placeholder (we use store mode in v1.1)', () => {
    const wrapper = mount(WriteWorkspaceEditorPane, {
      props: { content: '', editable: true },
      global: { stubs: { TipTapEditor: true } },
    })
    expect(wrapper.props('editable')).toBe(true)
  })
})