import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Phase 103 Task 8: chapter_overrides[].default_models column.
// Tests live alongside the component (existing convention — see
// `ProjectSettingsIllustration-chapter-overrides.spec.ts`,
// `ProjectSettingsIllustration-models.spec.ts`,
// `ProjectSettingsIllustration.spec.ts`).

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

vi.mock('@/api/illustrations', async () => {
  const actual = await vi.importActual<typeof import('@/api/illustrations')>(
    '@/api/illustrations'
  )
  return {
    ...actual,
    fetchProviderModels: fetchProviderModelsMock,
  }
})

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => ({
    settings: {
      default_provider: 'minimax',
      default_models: {},
      fallback_models: {},
      chapter_overrides: {},
      notify_threshold: 3,
    },
    save: storeMocks.saveMock,
    fetch: vi.fn(),
  }),
}))

const baseProps = () => ({
  style_preset: 'ink',
  auto_generate: false,
  max_assets: 10,
  confirm_before_generate: false,
  default_provider: 'minimax',
  default_models: {},
  fallback_models: {},
  chapter_overrides: {},
  notify_threshold: 3,
})

describe('ProjectSettingsIllustration — chapter_overrides[].default_models column (Phase 103 T8)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchProviderModelsMock.mockClear()
    storeMocks.saveMock.mockClear()
  })

  it('renders the new "Default Models" column header', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: { ...baseProps() },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const headers = wrapper.findAll('th')
    const defaultModelsHeader = headers.find((h) => h.text() === 'Default Models')
    expect(defaultModelsHeader).toBeTruthy()
  })

  it('renders existing provider-model pairs for a chapter', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          chapter_overrides: {
            1: { default_models: { openai: 'dall-e-3' } },
          },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const cell = wrapper.find('[data-testid="chapter-override-default-models-1"]')
    expect(cell.exists()).toBe(true)
    const pair = wrapper.find('[data-testid="chapter-override-default-model-pair-1-openai"]')
    expect(pair.exists()).toBe(true)
    const provider = wrapper.find(
      '[data-testid="chapter-override-default-model-provider-1-openai"]'
    )
    expect(provider.exists()).toBe(true)
    expect((provider.element as HTMLSelectElement).value).toBe('openai')
    const model = wrapper.find('[data-testid="chapter-override-default-model-name-1-openai"]')
    expect(model.exists()).toBe(true)
    expect((model.element as HTMLSelectElement).value).toBe('dall-e-3')
  })

  it('shows Add button when no default_models exist for chapter', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          chapter_overrides: { 5: { max_assets: 8 } },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const addBtn = wrapper.find('[data-testid="chapter-override-default-model-add-5"]')
    expect(addBtn.exists()).toBe(true)
    expect(addBtn.text()).toContain('+ Add')
  })

  it('emits update when remove button clicked', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          chapter_overrides: {
            1: { default_models: { openai: 'dall-e-3' } },
          },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const removeBtn = wrapper.find(
      '[data-testid="chapter-override-default-model-remove-1-openai"]'
    )
    expect(removeBtn.exists()).toBe(true)

    await removeBtn.trigger('click')
    await flushPromises()

    // Component propagates via store.save with new chapter_overrides dict
    // (immutable spread — original input is preserved). Use objectContaining
    // so we are robust against unrelated intermediate update() calls.
    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({
        chapter_overrides: expect.objectContaining({
          1: expect.objectContaining({ default_models: {} }),
        }),
      }),
    )
  })

  it('emits update via store.save when Add button clicked (seeds provider default_model)', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          chapter_overrides: { 5: {} },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const addBtn = wrapper.find('[data-testid="chapter-override-default-model-add-5"]')
    expect(addBtn.exists()).toBe(true)

    await addBtn.trigger('click')
    await flushPromises()

    // providers[0].id is 'minimax' (see ProjectSettingsIllustration.vue
    // providers const) and its mocked default_model is 'minimax-multimodal',
    // so Add seeds default_models['minimax'] with a non-empty string.
    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({
        chapter_overrides: expect.objectContaining({
          5: expect.objectContaining({
            default_models: expect.objectContaining({
              minimax: expect.any(String),
            }),
          }),
        }),
      }),
    )
  })

  it('emits update via store.save when model-name select changes', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          chapter_overrides: {
            1: { default_models: { openai: 'dall-e-3' } },
          },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const modelSelect = wrapper.find(
      '[data-testid="chapter-override-default-model-name-1-openai"]'
    )
    expect(modelSelect.exists()).toBe(true)

    // Set to a different model in the mocked openai catalog so we are not just
    // asserting "called with same value". 'dall-e-2' is in the mocked models
    // list (see fetchProviderModelsMock above).
    await modelSelect.setValue('dall-e-2')
    await flushPromises()

    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({
        chapter_overrides: expect.objectContaining({
          1: expect.objectContaining({
            default_models: expect.objectContaining({ openai: 'dall-e-2' }),
          }),
        }),
      }),
    )
  })

  it('preserves all other chapter_overrides columns alongside the new default_models column', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          chapter_overrides: {
            3: {
              max_assets: 8,
              confirm_before_generate: true,
              auto_generate: false,
              fallback_chain: ['stability'],
            },
          },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    // Phase 102 columns still rendered.
    expect(wrapper.find('[data-testid="chapter-override-max-assets-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chapter-override-confirm-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chapter-override-auto-generate-3"]').exists()).toBe(
      true
    )
    expect(wrapper.find('[data-testid="chapter-override-fallback-chain-3"]').exists()).toBe(true)
    // Phase 103 new column rendered.
    expect(wrapper.find('[data-testid="chapter-override-default-models-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chapter-override-default-model-add-3"]').exists()).toBe(
      true
    )
  })
})
