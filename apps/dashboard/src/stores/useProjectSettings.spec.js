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
    expect(store.settings).toEqual({ default_provider: 'minimax', fallback_chain: [] })
  })

  it('fetch falls back to defaults on network error', async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error('network'))
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({ default_provider: 'minimax', fallback_chain: [] })
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

  // Phase 98: PATCH semantics tests

  it('save(partial) merges with current settings (U1)', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        default_provider: 'minimax',
        max_assets: 5,
        auto_generate: true,
        confirm_before_generate: false,
      }),
    })
    const store = useProjectSettingsStore()
    store.settings = {
      default_provider: 'minimax',
      auto_generate: false,
      max_assets: 20,
      confirm_before_generate: false,
    }

    await store.save('test-slug', { max_assets: 5, auto_generate: true })

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/projects/test-slug/settings',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({
          default_provider: 'minimax',
          auto_generate: true,
          max_assets: 5,
          confirm_before_generate: false,
        }),
      }),
    )
  })

  it('save({default_provider}) preserves max_assets (U2)', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        default_provider: 'openai',
        max_assets: 20,
        auto_generate: false,
        confirm_before_generate: false,
      }),
    })
    const store = useProjectSettingsStore()
    store.settings = {
      default_provider: 'minimax',
      max_assets: 20,
      auto_generate: false,
      confirm_before_generate: false,
    }

    await store.save('test-slug', { default_provider: 'openai' })

    const callBody = JSON.parse(globalThis.fetch.mock.calls[0][1].body)
    expect(callBody.default_provider).toBe('openai')
    expect(callBody.max_assets).toBe(20) // preserved from current
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
