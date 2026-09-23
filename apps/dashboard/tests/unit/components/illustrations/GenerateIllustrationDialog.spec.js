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

describe('GenerateIllustrationDialog (Phase 96: provider picker)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('renders 3 provider options', () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 17, type: 'chapter', modelValue: true },
    })
    const providers = wrapper.findAll('[data-testid^="illustration-provider-"]')
    expect(providers.length).toBe(3)
    const ids = providers.map(p => p.attributes('data-testid'))
    expect(ids).toContain('illustration-provider-minimax')
    expect(ids).toContain('illustration-provider-openai')
    expect(ids).toContain('illustration-provider-stability')
  })

  it('defaults to minimax when no project default loaded', () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    })
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    expect(wrapper.vm.selectedProvider).toBe('minimax')
  })

  it('preselects provider from project default', async () => {
    // Phase 110 fix: use mockResolvedValue (default) instead of
    // mockResolvedValueOnce. The component makes TWO fetch calls on mount
    // (fetchProviderModels + store.fetch); once-mock is consumed by the
    // first call and the second call falls through to no-mock.
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    // Wait for store.fetch to resolve
    await new Promise(r => setTimeout(r, 10))
    expect(wrapper.vm.selectedProvider).toBe('openai')
  })

  it('emits provider in generate payload', async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    })
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    wrapper.vm.selectedProvider = 'stability'
    wrapper.vm.submit()
    const generated = wrapper.emitted('generate')
    expect(generated).toBeTruthy()
    expect(generated[0][0].provider).toBe('stability')
  })

  it('user can override provider per call', async () => {
    // Phase 110 fix: same as above — use mockResolvedValue (default) so
    // both fetch calls (model catalog + settings) return the openai shape.
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await new Promise(r => setTimeout(r, 10))
    wrapper.vm.selectedProvider = 'stability'  // override
    wrapper.vm.submit()
    const generated = wrapper.emitted('generate')
    expect(generated[0][0].provider).toBe('stability')
    // Verify NOT persisted to store
    expect(wrapper.vm.store.settings.default_provider).toBe('openai')
  })

  it('selects provider on click', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await wrapper.find('[data-testid="illustration-provider-openai"]').trigger('click')
    expect(wrapper.vm.selectedProvider).toBe('openai')
  })
})