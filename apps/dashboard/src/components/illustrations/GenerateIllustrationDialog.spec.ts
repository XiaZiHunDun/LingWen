import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import GenerateIllustrationDialog from './GenerateIllustrationDialog.vue'

// Mock the store module
vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => ({
    settings: { default_provider: 'minimax' },
    fetch: vi.fn().mockResolvedValue({ default_provider: 'minimax' }),
  }),
}))

describe('GenerateIllustrationDialog — reference image toggle', () => {
  beforeEach(() => {
    globalThis.$fetch = vi.fn().mockResolvedValue({ default_provider: 'minimax' })
  })

  it('renders use-project-reference checkbox', () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    expect(wrapper.find('[data-testid="dialog-use-project-reference"]').exists()).toBe(true)
  })

  it('renders per-call file input', () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    expect(wrapper.find('[data-testid="dialog-per-call-reference"]').exists()).toBe(true)
  })

  it('emits generate event with use_project_reference=true by default', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await flushPromises()
    await wrapper.find('[data-testid="generate-submit"]').trigger('click')
    const events = wrapper.emitted('generate')
    expect(events).toBeTruthy()
    expect(events[0][0].use_project_reference).toBe(true)
  })

  it('emits generate with per_call_reference when file selected', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    const file = new File(['x'], 'ref.jpg', { type: 'image/jpeg' })
    const input = wrapper.find('[data-testid="dialog-per-call-reference"]')
    Object.defineProperty(input.element, 'files', { value: [file], writable: false })
    await input.trigger('change')
    await wrapper.find('[data-testid="generate-submit"]').trigger('click')
    const payload = wrapper.emitted('generate')[0][0]
    expect(payload.per_call_reference).toBe(file)
  })

  it('shows openai rejection warning when openai selected + project reference', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 1, modelValue: true },
    })
    await flushPromises()
    // Switch to openai
    await wrapper.find('[data-testid="illustration-provider-openai"]').trigger('click')
    await flushPromises()
    // Warning text should appear
    expect(wrapper.html()).toContain('OpenAI')
  })
})
