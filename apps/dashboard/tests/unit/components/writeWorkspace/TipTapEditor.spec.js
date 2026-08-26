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
})
