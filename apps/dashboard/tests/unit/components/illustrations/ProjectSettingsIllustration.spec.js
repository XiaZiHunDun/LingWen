import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
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

describe('ProjectSettingsIllustration (Phase 96: provider dropdown)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('renders default_provider dropdown with three options', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...defaults,
          default_provider: 'minimax',
        },
        slug: 'test',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    expect(select.exists()).toBe(true)
    const options = select.findAll('option')
    expect(options.length).toBe(3)
    expect(options.map(o => o.attributes('value'))).toEqual(['minimax', 'openai', 'stability'])
  })

  it('selects current default_provider value', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...defaults,
          default_provider: 'openai',
        },
        slug: 'test',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    expect(select.element.value).toBe('openai')
  })

  it('emits update:modelValue when provider changed', async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ default_provider: 'stability' }),
    })
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...defaults,
          default_provider: 'minimax',
        },
        slug: 'test',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    await select.setValue('stability')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    const last = wrapper.emitted('update:modelValue').at(-1)[0]
    expect(last.default_provider).toBe('stability')
  })

  it('persists via store.save when provider changed', async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...defaults,
          default_provider: 'minimax',
        },
        slug: 'test-slug',
      },
    })
    const select = wrapper.find('[data-testid="project-settings-illustration-default-provider"]')
    await select.setValue('openai')
    // Wait for async save to fire
    await new Promise(r => setTimeout(r, 10))
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/settings',
      expect.objectContaining({ method: 'PUT' }),
    )
  })
})
