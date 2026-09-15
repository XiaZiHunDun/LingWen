import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import GenerateIllustrationDialog from '@/components/illustrations/GenerateIllustrationDialog.vue'

describe('GenerateIllustrationDialog', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders 3 style preset options', () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 17, type: 'chapter', modelValue: true },
    })
    const presets = wrapper.findAll('[data-testid^="style-preset-"]')
    expect(presets.length).toBe(3)
  })

  it('selects preset on click', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 17, type: 'chapter', modelValue: true },
    })
    await wrapper.find('[data-testid="style-preset-ink"]').trigger('click')
    expect(wrapper.vm.selectedPreset).toBe('ink')
  })

  it('emits generate event with params on submit', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 17, type: 'chapter', modelValue: true },
    })
    wrapper.vm.selectedPreset = 'ink'
    wrapper.vm.customPrompt = '远景镜头'

    await wrapper.find('[data-testid="generate-submit"]').trigger('click')
    expect(wrapper.emitted('generate')).toBeTruthy()
    expect(wrapper.emitted('generate')[0][0]).toMatchObject({
      type: 'chapter',
      chapter_num: 17,
      style_preset: 'ink',
      custom_prompt: '远景镜头',
    })
  })
})