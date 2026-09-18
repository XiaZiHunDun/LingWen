import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ReferenceImageUpload from './ReferenceImageUpload.vue'

// Mock the store module before importing the component.
// NOTE: referenceImage is a plain value (not a Vue ref) — Pinia stores expose
// state as auto-unwrapped values, and Vue's template compiler only auto-unwraps
// refs returned from setup() (not refs nested inside plain objects).
const mockStore = {
  fetchReferenceImage: vi.fn(),
  fetchReferenceImageBlob: vi.fn(),
  uploadReferenceImage: vi.fn(),
  deleteReferenceImage: vi.fn(),
  referenceImage: null,
}

vi.mock('@/stores/useProjectSettings.js', () => ({
  useProjectSettingsStore: () => mockStore,
}))

describe('ReferenceImageUpload', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockStore.referenceImage = null
  })

  it('renders upload button when no image set', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-upload-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="reference-image-preview"]').exists()).toBe(false)
  })

  it('renders preview when image exists', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue({
      exists: true,
      size_bytes: 1024,
      mime_type: 'image/jpeg',
    })
    // Store contract: returns raw Blob; component wraps with URL.createObjectURL.
    mockStore.fetchReferenceImageBlob.mockResolvedValue(new Blob(['fake-bytes'], { type: 'image/jpeg' }))
    mockStore.referenceImage = {
      exists: true,
      size_bytes: 1024,
      mime_type: 'image/jpeg',
    }
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-preview"]').exists()).toBe(true)
  })

  it('calls uploadReferenceImage on file change', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    mockStore.uploadReferenceImage.mockResolvedValue(undefined)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()

    const file = new File(['fake-bytes'], 'test.jpg', { type: 'image/jpeg' })
    const input = wrapper.find('[data-testid="reference-image-upload-input"]')
    // Use Object.defineProperty to set files on input
    Object.defineProperty(input.element, 'files', { value: [file], writable: false })
    await input.trigger('change')

    expect(mockStore.uploadReferenceImage).toHaveBeenCalledWith('test', file)
  })

  it('calls deleteReferenceImage on remove click', async () => {
    mockStore.referenceImage = {
      exists: true,
      size_bytes: 1024,
      mime_type: 'image/jpeg',
    }
    mockStore.deleteReferenceImage.mockResolvedValue(undefined)
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()

    await wrapper.find('[data-testid="reference-image-remove"]').trigger('click')
    expect(mockStore.deleteReferenceImage).toHaveBeenCalledWith('test')
  })

  it('displays error message on upload failure', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    mockStore.uploadReferenceImage.mockRejectedValue({
      data: { detail: { error: 'file too large' } },
    })
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()

    const file = new File(['fake-bytes'], 'big.jpg', { type: 'image/jpeg' })
    const input = wrapper.find('[data-testid="reference-image-upload-input"]')
    Object.defineProperty(input.element, 'files', { value: [file], writable: false })
    await input.trigger('change')
    await flushPromises()
    expect(wrapper.find('[data-testid="reference-image-error"]').exists()).toBe(true)
  })

  it('contains reference-image-upload data-testid marker', async () => {
    mockStore.fetchReferenceImage.mockResolvedValue(null)
    const wrapper = mount(ReferenceImageUpload, { props: { slug: 'test' } })
    await flushPromises()
    const html = wrapper.html()
    expect(html).toContain('reference-image-upload')
    expect(html).toContain('reference-image-upload-input')
    expect(html).toContain('reference-image-upload-button')
  })
})
