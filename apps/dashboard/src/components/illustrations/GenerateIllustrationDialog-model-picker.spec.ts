// Phase 100 Task 9: model picker filtered by provider.
//
// The existing dialog (Phase 90/96/97/98) uses:
//   - Button-group provider UI with `data-testid="illustration-provider-{id}"`
//   - Checkbox reference toggle with `data-testid="dialog-use-project-reference"`
//
// So we click those existing elements (not setValue on a select that doesn't
// exist) and then verify the NEW model <select data-testid="model-select">
// is rendered + populated + disabled under the expected conditions.
//
// fetchProviderModels is mocked per-provider so each test controls which
// catalog comes back for each provider selection.

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Phase 100 Task 9: model picker filtered by provider.
//
// The existing dialog (Phase 90/96/97/98) uses:
//   - Button-group provider UI with `data-testid="illustration-provider-{id}"`
//   - Checkbox reference toggle with `data-testid="dialog-use-project-reference"`
//
// So we click those existing elements (not setValue on a select that doesn't
// exist) and then verify the NEW model <select data-testid="model-select">
// is rendered + populated + disabled under the expected conditions.
//
// fetchProviderModels is mocked per-provider so each test controls which
// catalog comes back for each provider selection. The dialog is loaded via
// dynamic import (per Phase 100 T8 / existing pattern in this folder) so the
// vi.mock factory runs before the dialog module is resolved.

const fetchProviderModelsMock = vi.fn(async (name: string) => {
  const catalogs: Record<string, { provider: string; models: string[]; default_model: string }> = {
    minimax: {
      provider: 'minimax',
      models: ['minimax-multimodal'],
      default_model: 'minimax-multimodal',
    },
    openai: {
      provider: 'openai',
      models: ['dall-e-3', 'dall-e-3-hd', 'gpt-image-1'],
      default_model: 'dall-e-3',
    },
    stability: {
      provider: 'stability',
      models: ['sd3-medium', 'sd3-large'],
      default_model: 'sd3-medium',
    },
  }
  return catalogs[name]
})

vi.mock('@/api/illustrations', () => ({
  fetchProviderModels: fetchProviderModelsMock,
}))

// Phase 98 mutable per-test settings pattern (matches existing spec).
let mockSettings = {
  default_provider: 'minimax',
  default_models: {},
  confirm_before_generate: false,
}

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => ({
    settings: mockSettings,
    fetch: vi.fn().mockResolvedValue(mockSettings),
    save: vi.fn(),
  }),
}))

describe('GenerateIllustrationDialog — model picker (Phase 100 T9)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockSettings = {
      default_provider: 'minimax',
      default_models: {},
      confirm_before_generate: false,
    }
    globalThis.$fetch = vi.fn().mockResolvedValue(mockSettings)
    fetchProviderModelsMock.mockClear()
  })

  it('shows model picker when provider is selected (catalog fetched)', async () => {
    const { default: GenerateIllustrationDialog } = await import(
      './GenerateIllustrationDialog.vue'
    )
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    // First flush: project settings fetch + immediate catalog fetch on
    // selectedProvider=minimax (default). Second flush: any chained promise.
    await flushPromises()
    await flushPromises()

    // Switch to openai (button-group UI, not a <select>)
    await wrapper.find('[data-testid="illustration-provider-openai"]').trigger('click')
    await flushPromises()
    await flushPromises()

    const modelSelect = wrapper.find('[data-testid="model-select"]')
    expect(modelSelect.exists()).toBe(true)
  })

  it('filters model options by selected provider', async () => {
    const { default: GenerateIllustrationDialog } = await import(
      './GenerateIllustrationDialog.vue'
    )
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await flushPromises()
    await flushPromises()

    // Switch to stability
    await wrapper.find('[data-testid="illustration-provider-stability"]').trigger('click')
    await flushPromises()
    await flushPromises()

    const modelSelect = wrapper.find('[data-testid="model-select"]')
    expect(modelSelect.exists()).toBe(true)
    const optionTexts = modelSelect.findAll('option').map((o) => o.text())
    expect(optionTexts).toContain('sd3-medium')
    expect(optionTexts).toContain('sd3-large')
    expect(optionTexts).not.toContain('dall-e-3')
    expect(optionTexts).not.toContain('gpt-image-1')
  })

  it('disables model picker when use_project_reference=true (i2i path)', async () => {
    const { default: GenerateIllustrationDialog } = await import(
      './GenerateIllustrationDialog.vue'
    )
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await flushPromises()
    await flushPromises()

    // useProjectReference defaults to true → model select is disabled from
    // the moment the catalog is fetched on mount (selectedProvider=minimax).
    const modelSelect = wrapper.find('[data-testid="model-select"]')
    expect(modelSelect.exists()).toBe(true)
    expect(modelSelect.attributes('disabled')).toBeDefined()

    // Toggle i2i off → model picker should re-enable.
    const refToggle = wrapper.find('[data-testid="dialog-use-project-reference"]')
    expect(refToggle.exists()).toBe(true)
    await refToggle.setValue(false)
    await flushPromises()

    expect(modelSelect.attributes('disabled')).toBeUndefined()
  })
})

