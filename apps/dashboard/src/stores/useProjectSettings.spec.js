import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectSettingsStore } from './useProjectSettings.js'

describe('useProjectSettingsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('fetch loads settings from API', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ default_provider: 'openai' }),
    })
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({ default_provider: 'openai' })
    expect(store.slug).toBe('test-slug')
  })

  it('fetch falls back to defaults on 404', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({}),
    })
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({ default_provider: 'minimax' })
  })

  it('fetch falls back to defaults on network error', async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error('network'))
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({ default_provider: 'minimax' })
  })

  it('save persists to API', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ default_provider: 'stability' }),
    })
    const store = useProjectSettingsStore()
    store.settings = { default_provider: 'minimax' }
    await store.save('test-slug', { default_provider: 'stability' })
    expect(store.settings).toEqual({ default_provider: 'stability' })
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/settings',
      expect.objectContaining({ method: 'PUT' }),
    )
  })

  it('save throws on non-ok response', async () => {
    globalThis.fetch.mockResolvedValueOnce({ ok: false, status: 500 })
    const store = useProjectSettingsStore()
    store.settings = { default_provider: 'minimax' }
    await expect(store.save('test-slug', { default_provider: 'openai' }))
      .rejects.toThrow('save failed: 500')
  })
})

describe('useProjectSettingsStore — reference image methods (Phase 97)', () => {
  it('fetchReferenceImage populates state and returns info', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ exists: true, size_bytes: 1024, mime_type: 'image/jpeg' }),
    })
    const store = useProjectSettingsStore()
    const result = await store.fetchReferenceImage('test-slug')
    expect(result.exists).toBe(true)
    expect(result.size_bytes).toBe(1024)
    expect(store.referenceImage.exists).toBe(true)
    expect(store.referenceImage.size_bytes).toBe(1024)
  })

  it('fetchReferenceImage returns null on 404 and clears state', async () => {
    globalThis.fetch.mockResolvedValueOnce({ ok: false, status: 404 })
    const store = useProjectSettingsStore()
    const result = await store.fetchReferenceImage('test-slug')
    expect(result).toBe(null)
    expect(store.referenceImage).toBe(null)
  })

  it('uploadReferenceImage posts FormData to reference-image endpoint', async () => {
    globalThis.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    const store = useProjectSettingsStore()
    const file = new File(['x'], 'test.jpg', { type: 'image/jpeg' })
    await store.uploadReferenceImage('test-slug', file)
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/reference-image',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('deleteReferenceImage clears state', async () => {
    globalThis.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ deleted: true }) })
    const store = useProjectSettingsStore()
    store.referenceImage = { exists: true, size_bytes: 1, mime_type: 'image/jpeg' }
    await store.deleteReferenceImage('test-slug')
    expect(store.referenceImage).toBe(null)
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/reference-image',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })

  it('fetchReferenceImageBlob returns blob from response', async () => {
    const fakeBlob = new Blob(['fake-bytes'], { type: 'image/jpeg' })
    globalThis.fetch.mockResolvedValueOnce({ ok: true, blob: async () => fakeBlob })
    const store = useProjectSettingsStore()
    const result = await store.fetchReferenceImageBlob('test-slug')
    expect(result).toBe(fakeBlob)
  })
})
