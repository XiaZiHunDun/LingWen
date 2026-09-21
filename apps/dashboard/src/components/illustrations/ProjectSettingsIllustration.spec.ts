import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Phase 97 (ReferenceImageUpload), Phase 102 (notify_threshold slider),
// Phase 103 (chapter_overrides default_models), Phase 104 (notify_threshold
// per-event-type table) — all in one file per the existing convention.

// vi.hoisted: shared mutable mocks so each describe block can introspect
// store.save() calls. vi.mock factories are hoisted to the top of the file,
// so any spy used inside must also live in hoisted space.
const storeMocks = vi.hoisted(() => ({
  saveMock: vi.fn().mockResolvedValue(undefined),
}))

const fetchProviderModelsMock = vi.fn(async (name: string) => {
  const catalogs: Record<
    string,
    { provider: string; models: string[]; default_model: string }
  > = {
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
      notify_threshold: { generation: 3, regeneration: 3, cleanup: 3, deletion: 3 },
    },
    save: storeMocks.saveMock,
    fetch: vi.fn(),
  }),
}))

describe('ProjectSettingsIllustration — reference image integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    storeMocks.saveMock.mockClear()
  })

  it('embeds ReferenceImageUpload component', async () => {
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
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-upload"]').exists()).toBe(true)
  })

  it('reference image upload renders before max_assets field', async () => {
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

// Phase 104 Task 8: Notify Thresholds subsection (4-row keyed table replacing
// the Phase 102 single slider).
const phase104BaseProps = () => ({
  style_preset: 'ink' as const,
  auto_generate: false,
  max_assets: 10,
  confirm_before_generate: false,
  default_provider: 'minimax' as const,
  default_models: {},
  fallback_models: {},
  chapter_overrides: {},
  notify_threshold: {
    generation: 3,
    regeneration: 3,
    cleanup: 3,
    deletion: 3,
  },
})

describe('ProjectSettingsIllustration — Notify Thresholds subsection (Phase 104 T8)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchProviderModelsMock.mockClear()
    storeMocks.saveMock.mockClear()
  })

  it('renders 4 rows with current values', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...phase104BaseProps(),
          notify_threshold: { generation: 5, regeneration: 5 },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    expect(
      wrapper.find('[data-testid="notify-threshold-row-generation"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="notify-threshold-row-regeneration"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="notify-threshold-row-cleanup"]').exists()
    ).toBe(true)
    expect(
      wrapper.find('[data-testid="notify-threshold-row-deletion"]').exists()
    ).toBe(true)
    expect(
      wrapper
        .find('[data-testid="notify-threshold-input-generation"]')
        .element.value
    ).toBe('5')
    // configured regeneration row also reads 5
    expect(
      wrapper
        .find('[data-testid="notify-threshold-input-regeneration"]')
        .element.value
    ).toBe('5')
    // unconfigured cleanup + deletion show empty (opt-out / ∞)
    expect(
      wrapper.find('[data-testid="notify-threshold-input-cleanup"]').element.value
    ).toBe('')
    expect(
      wrapper.find('[data-testid="notify-threshold-input-deletion"]').element.value
    ).toBe('')
  })

  it('NumberInput change updates dict and persists via store.save', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...phase104BaseProps(),
          notify_threshold: { generation: 3 },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const input = wrapper.find('[data-testid="notify-threshold-input-generation"]')
    expect(input.exists()).toBe(true)

    await input.setValue('10')
    await flushPromises()

    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({
        notify_threshold: expect.objectContaining({ generation: 10 }),
      }),
    )
  })

  it('reset-all button sets all 4 to 3', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    // Wrap ProjectSettingsIllustration in a parent that owns modelValue so the
    // emitted `update:modelValue` actually feeds back into the prop (mirrors
    // the production <ProjectSettingsIllustration v-model="settings" /> wiring
    // in SettingsPage.vue). Without this wrapper, the displayed input values
    // would never reflect the post-reset state because props.modelValue is
    // one-way bound and the test has no real parent listener.
    const Parent = {
      components: { ProjectSettingsIllustration },
      data: () => ({
        settings: {
          ...phase104BaseProps(),
          notify_threshold: { generation: 1 },
        },
        slug: 'test-slug',
      }),
      template: `<ProjectSettingsIllustration v-model="settings" :slug="slug" />`,
    }
    const wrapper = mount(Parent)
    await flushPromises()
    await flushPromises()

    const resetBtn = wrapper.find('[data-testid="notify-threshold-reset-all"]')
    expect(resetBtn.exists()).toBe(true)

    await resetBtn.trigger('click')
    await flushPromises()

    // All 4 rows now show 3 (the default) and the store saw the dict shape.
    for (const et of ['generation', 'regeneration', 'cleanup', 'deletion']) {
      expect(
        wrapper.find(`[data-testid="notify-threshold-input-${et}"]`).element.value
      ).toBe('3')
    }
    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({
        notify_threshold: {
          generation: 3,
          regeneration: 3,
          cleanup: 3,
          deletion: 3,
        },
      }),
    )
  })

  it('empty input displays "∞" placeholder and opt-out removes key on change', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...phase104BaseProps(),
          notify_threshold: { generation: 5 },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    const input = wrapper.find('[data-testid="notify-threshold-input-cleanup"]')
    expect(input.exists()).toBe(true)
    // cleanup is unconfigured → empty value + ∞ placeholder
    expect(input.element.value).toBe('')
    expect(input.attributes('placeholder')).toBe('∞')

    // Empty input on the configured `generation` row → opt-out (key removed).
    const genInput = wrapper.find('[data-testid="notify-threshold-input-generation"]')
    await genInput.setValue('')
    await flushPromises()

    expect(storeMocks.saveMock).toHaveBeenCalledWith(
      'test-slug',
      expect.objectContaining({
        notify_threshold: expect.not.objectContaining({ generation: expect.anything() }),
      }),
    )
  })

  it('legacy int response shows same threshold in all 4 rows', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    // Stale API / cache may still surface a bare int — UI handles this
    // defensively by rendering the same number in every row.
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...phase104BaseProps(),
          notify_threshold: 5 as unknown as Record<string, number>,
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    for (const et of ['generation', 'regeneration', 'cleanup', 'deletion']) {
      expect(
        wrapper.find(`[data-testid="notify-threshold-input-${et}"]`).element.value
      ).toBe('5')
    }
  })

  it('partial dict response shows empty cells for unconfigured types', async () => {
    const { default: ProjectSettingsIllustration } = await import(
      './ProjectSettingsIllustration.vue'
    )
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          ...phase104BaseProps(),
          notify_threshold: { generation: 5 },
        },
        slug: 'test-slug',
      },
    })
    await flushPromises()
    await flushPromises()

    expect(
      wrapper.find('[data-testid="notify-threshold-input-generation"]').element.value
    ).toBe('5')
    expect(
      wrapper.find('[data-testid="notify-threshold-input-regeneration"]').element
        .value
    ).toBe('')
    expect(
      wrapper.find('[data-testid="notify-threshold-input-cleanup"]').element.value
    ).toBe('')
    expect(
      wrapper.find('[data-testid="notify-threshold-input-deletion"]').element.value
    ).toBe('')
  })
})
