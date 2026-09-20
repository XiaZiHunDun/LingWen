import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Phase 102 T10: chapter_overrides per-chapter subset merge UI.
// Phase 102 T11: notify_threshold slider for consecutive failure warning.
//
// Tests live alongside the component (existing convention — see
// `ProjectSettingsIllustration.spec.ts`, `ReferenceImageUpload.spec.ts`,
// `GenerateIllustrationDialog.spec.ts`, `ProjectSettingsIllustration-models.spec.ts`).

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

describe('ProjectSettingsIllustration — chapter_overrides section (Phase 102 T10)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchProviderModelsMock.mockClear()
    storeMocks.saveMock.mockClear()
  })

  it('renders chapter_overrides section with at least 1 row when populated', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          chapter_overrides: { 1: { max_assets: 5 } },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    expect(
      wrapper.find('[data-testid="chapter-overrides-section"]').exists()
    ).toBe(true)
    const rows = wrapper.findAll('[data-testid^="chapter-override-row-"]')
    expect(rows.length).toBeGreaterThanOrEqual(1)
  })

  it('add chapter override row on + Add chapter click', async () => {
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

    const addBtn = wrapper.find('[data-testid="add-chapter-override"]')
    expect(addBtn.exists()).toBe(true)

    // Click — component emits update + calls store.save with new override dict.
    await addBtn.trigger('click')
    await flushPromises()

    // Verify save was called with the next monotonic chapter number (1).
    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({
        chapter_overrides: expect.objectContaining({ 1: {} }),
      }),
    )
  })

  it('remove chapter override row on × click', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...baseProps(),
          // Pre-populate with 1 row so remove has something to act on.
          chapter_overrides: { 1: { max_assets: 5 } },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const removeBtn = wrapper.find('[data-testid="chapter-override-remove-1"]')
    expect(removeBtn.exists()).toBe(true)

    await removeBtn.trigger('click')
    await flushPromises()

    // Verify save was called with chapter_overrides emptied.
    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({ chapter_overrides: {} }),
    )
  })
})

describe('ProjectSettingsIllustration — notify_threshold slider (Phase 102 T11)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchProviderModelsMock.mockClear()
    storeMocks.saveMock.mockClear()
  })

  it('renders notify_threshold slider', async () => {
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

    expect(
      wrapper.find('[data-testid="notify-threshold-slider"]').exists()
    ).toBe(true)
    // Also verify the wrapping section is present.
    expect(
      wrapper.find('[data-testid="notify-threshold-section"]').exists()
    ).toBe(true)
  })

  it('updates notify_threshold via slider and persists via store.save', async () => {
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

    const slider = wrapper.find('[data-testid="notify-threshold-slider"]')
    expect(slider.exists()).toBe(true)

    // setValue triggers @input on the range input; updateNotifyThreshold clamps
    // to 1-10 and round-trips through update() → store.save().
    await slider.setValue('5')
    await flushPromises()

    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({ notify_threshold: 5 }),
    )
  })
})
