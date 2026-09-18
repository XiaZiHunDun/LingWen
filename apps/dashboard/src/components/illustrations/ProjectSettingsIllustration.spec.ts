import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ProjectSettingsIllustration from './ProjectSettingsIllustration.vue'

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => ({
    settings: { default_provider: 'minimax' },
    save: vi.fn(),
  }),
}))

describe('ProjectSettingsIllustration — reference image integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('embeds ReferenceImageUpload component', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-upload"]').exists()).toBe(true)
  })

  it('reference image upload renders before max_assets field', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
        },
        slug: 'test-slug',
      },
    })
    const html = wrapper.html()
    const refIdx = html.indexOf('reference-image-upload')
    const maxIdx = html.indexOf('project-settings-illustration-max-assets')
    expect(refIdx).toBeGreaterThan(-1)
    expect(maxIdx).toBeGreaterThan(refIdx)
  })

  it('default_provider still works (no regression)', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
          default_provider: 'minimax',
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    expect(
      wrapper.find('[data-testid="project-settings-illustration-default-provider"]').exists()
    ).toBe(true)
  })
})
