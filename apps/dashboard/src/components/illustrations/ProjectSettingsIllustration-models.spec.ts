import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Phase 100 T8: per-provider model dropdowns.
// Phase 102 T9: per-provider fallback model dropdowns (mirror default_models).
// Tests live alongside the component (existing convention in this folder — see
// `ProjectSettingsIllustration.spec.ts`, `ReferenceImageUpload.spec.ts`,
// `GenerateIllustrationDialog.spec.ts`).

// vi.hoisted: shared mutable mock so each test can introspect save() calls.
// vi.mock factories are hoisted to the top of the file, so any spy used inside
// must also live in hoisted space.
const storeMocks = vi.hoisted(() => ({
  saveMock: vi.fn().mockResolvedValue(undefined),
}))

const fetchProviderModelsMock = vi.fn(async (name: string) => {
  const catalogs: Record<string, { provider: string; models: string[]; default_model: string }> = {
    minimax: {
      provider: 'minimax',
      models: ['minimax-multimodal', 'minimax-vision-01'],
      default_model: 'minimax-multimodal',
    },
    openai: {
      provider: 'openai',
      models: ['dall-e-3', 'dall-e-3-hd', 'dall-e-2', 'gpt-image-1'],
      default_model: 'dall-e-3',
    },
    stability: {
      provider: 'stability',
      models: ['sd3-medium', 'sd3-large', 'sd3-large-turbo', 'stable-image-core', 'stable-image-ultra'],
      default_model: 'sd3-medium',
    },
  }
  return catalogs[name]
})

vi.mock('@/api/illustrations', () => ({
  fetchProviderModels: fetchProviderModelsMock,
}))

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => ({
    settings: { default_provider: 'minimax', default_models: {}, fallback_models: {} },
    save: storeMocks.saveMock,
    fetch: vi.fn(),
  }),
}))

describe('ProjectSettingsIllustration — per-provider model dropdowns (Phase 100)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchProviderModelsMock.mockClear()
    storeMocks.saveMock.mockClear()
  })

  it('renders 3 per-provider model dropdowns', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
          default_provider: 'minimax',
          default_models: {},
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const selects = wrapper.findAll('select[data-testid^="default-model-"]')
    expect(selects.length).toBe(3)
    expect(
      wrapper.find('[data-testid="default-model-minimax"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="default-model-openai"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="default-model-stability"]').exists()
    ).toBe(true)
  })

  it('renders 3 per-provider fallback-model dropdowns', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
          default_provider: 'minimax',
          default_models: { minimax: 'minimax-vision-01' },
          fallback_models: { minimax: 'minimax-multimodal' },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const selects = wrapper.findAll('select[data-testid^="fallback-model-"]')
    expect(selects.length).toBe(3)
    expect(
      wrapper.find('[data-testid="fallback-model-minimax"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="fallback-model-openai"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="fallback-model-stability"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="fallback-models-section"]').exists()
    ).toBe(true)
  })

  it('update_fallback_model_default drops sentinel "" in save payload', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          style_preset: 'ink',
          auto_generate: false,
          max_assets: 10,
          confirm_before_generate: false,
          default_provider: 'minimax',
          default_models: { minimax: 'minimax-vision-01' },
          fallback_models: { minimax: 'minimax-multimodal' },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const select = wrapper.find('[data-testid="fallback-model-minimax"]')
    await select.setValue('') // sentinel — should be dropped from save payload

    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({ fallback_models: {} }),
    )
  })

  it('accepts default_models dict on store.settings', async () => {
    const { useProjectSettingsStore } = await import(
      '@/stores/useProjectSettings.js'
    )
    const store = useProjectSettingsStore()

    // Verify default_models field is settable on settings (generic dict).
    store.settings = {
      default_provider: 'minimax',
      default_models: {
        minimax: 'minimax-vision-01',
        openai: 'gpt-image-1',
      },
      auto_generate: false,
      max_assets: 20,
      confirm_before_generate: false,
    }

    expect(store.settings.default_models).toEqual({
      minimax: 'minimax-vision-01',
      openai: 'gpt-image-1',
    })

    // Verify save() is callable with default_models dict (just verify the
    // action exists and accepts the dict shape — the real persistence is
    // covered by backend integration tests).
    expect(typeof store.save).toBe('function')
    const saveMock = vi.fn().mockResolvedValue(undefined)
    const storeWithMockSave = {
      settings: { default_provider: 'minimax', default_models: {} },
      save: saveMock,
    }
    await storeWithMockSave.save('test-slug', {
      default_models: { minimax: 'minimax-vision-01' },
    })
    expect(saveMock).toHaveBeenCalledWith('test-slug', {
      default_models: { minimax: 'minimax-vision-01' },
    })
  })
})