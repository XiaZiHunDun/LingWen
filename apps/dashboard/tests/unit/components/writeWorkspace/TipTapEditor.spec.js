import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import TipTapEditor from '@/components/writeWorkspace/TipTapEditor.vue'

describe('TipTapEditor', () => {
  it('mounts without throwing', () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: '' },
      global: { stubs: { EditorContent: true } },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('emits update:modelValue when content changes', async () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: 'initial' },
      global: { stubs: { EditorContent: true } },
    })
    wrapper.vm.handleUpdate('new content')
    await nextTick()
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['new content'])
  })

  it('renders Chinese punctuation without crashing', () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: '雨下得很大，「师叔——」她低声说。' },
      global: { stubs: { EditorContent: true } },
    })
    expect(wrapper.exists()).toBe(true)
  })

  // NEW: actually invokes insertSceneBreak against a real editor
  it('insertSceneBreak inserts a scene break into editor HTML', async () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: '<p>前面</p>' },
      global: { stubs: { EditorContent: true } },
    })
    wrapper.vm.insertSceneBreak()
    await nextTick()
    const html = wrapper.vm.editor?.getHTML() || ''
    expect(html).toContain('data-scene-break')
  })

  // NEW: editable prop is reactive
  it('editable prop change updates editor editable state', async () => {
    const wrapper = mount(TipTapEditor, {
      props: { modelValue: '', editable: true },
      global: { stubs: { EditorContent: true } },
    })
    expect(wrapper.vm.editor?.isEditable).toBe(true)
    await wrapper.setProps({ editable: false })
    expect(wrapper.vm.editor?.isEditable).toBe(false)
  })
})
