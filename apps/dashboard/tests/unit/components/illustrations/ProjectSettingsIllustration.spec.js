import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ProjectSettingsIllustration from '@/components/illustrations/ProjectSettingsIllustration.vue'

const defaults = {
  style_preset: 'ink',
  auto_generate: false,
  max_assets: 200,
  confirm_before_generate: true,
}

describe('ProjectSettingsIllustration', () => {
  it('renders 3 default style options', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: { modelValue: { ...defaults } },
    })
    const presets = wrapper.findAll('[data-testid^="project-settings-illustration-default-style-"]')
    expect(presets).toHaveLength(3)
  })

  it('marks the active style preset as selected', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: { modelValue: { ...defaults, style_preset: 'anime' } },
    })
    const animeBtn = wrapper.find('[data-testid="project-settings-illustration-default-style-anime"]')
    expect(animeBtn.classes()).toContain('selected')
  })

  it('emits update:modelValue with new style_preset on preset click', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: { modelValue: { ...defaults } },
    })
    await wrapper.find('[data-testid="project-settings-illustration-default-style-realistic"]').trigger('click')
    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted).toBeTruthy()
    expect(emitted[emitted.length - 1][0]).toMatchObject({ style_preset: 'realistic' })
  })

  it('emits update on auto-generate toggle', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: { modelValue: { ...defaults } },
    })
    await wrapper.find('[data-testid="project-settings-illustration-auto-generate"]').setValue(true)
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})