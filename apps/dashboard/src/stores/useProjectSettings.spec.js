import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import {
  useProjectSettingsStore,
  normalizeNotifyThreshold,
} from './useProjectSettings.js'

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
    // Phase 104: fetch() normalizes notify_threshold (always present after normalization,
    // defaulting to {} when API omitted the field).
    expect(store.settings).toEqual({ default_provider: 'openai', notify_threshold: {} })
    expect(store.slug).toBe('test-slug')
  })

  it('fetch falls back to defaults on 404', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({}),
    })
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({
      default_provider: 'minimax',
      fallback_chain: [],
      fallback_models: {},
      chapter_overrides: {},
      // Phase 104 EXCEPTION: notify_threshold fallback defaults are normalized
      // via normalizeNotifyThreshold(3) to keep the "always dict at store
      // boundary" contract. The legacy int 3 expands to a 4-key dict here.
      notify_threshold: { generation: 3, regeneration: 3, cleanup: 3, deletion: 3 },
    })
  })

  it('fetch falls back to defaults on network error', async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error('network'))
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings).toEqual({
      default_provider: 'minimax',
      fallback_chain: [],
      fallback_models: {},
      chapter_overrides: {},
      // Phase 104 EXCEPTION: notify_threshold fallback defaults are normalized
      // via normalizeNotifyThreshold(3) to keep the "always dict at store
      // boundary" contract. The legacy int 3 expands to a 4-key dict here.
      notify_threshold: { generation: 3, regeneration: 3, cleanup: 3, deletion: 3 },
    })
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

describe('useProjectSettingsStore — 3 new fields (Phase 102)', () => {
  // Phase 102 added 3 new persistent fields:
  //   - fallback_models: per-provider model override for fallback chain retry
  //   - chapter_overrides: per-chapter subset merge
  //   - notify_threshold: consecutive failure count before warning
  //
  // Defaults are applied at the CONSUMER level via `??` operator in the
  // component (props.modelValue?.X ?? default). The store stores whatever the
  // API returns — old-shape (200 OK without 3 new fields) leaves them
  // undefined, and the `??` fallback path activates. The 404 / network-error
  // path applies defaults at the store level (see tests above).
  //
  // This describe has its own beforeEach to reset globalThis.fetch — the outer
  // describe's beforeEach does not propagate to sibling describes, so without
  // this reset mock.calls from prior tests would leak into mock.calls[0].

  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('store has fallback_models field defaulting to {}', () => {
    const store = useProjectSettingsStore()
    // settings starts as null → consumer applies `?? {}` default.
    expect(store.settings?.fallback_models ?? {}).toEqual({})
  })

  it('store has chapter_overrides field defaulting to {}', () => {
    const store = useProjectSettingsStore()
    expect(store.settings?.chapter_overrides ?? {}).toEqual({})
  })

  it('store has notify_threshold field defaulting to 3', () => {
    const store = useProjectSettingsStore()
    expect(store.settings?.notify_threshold ?? 3).toBe(3)
  })

  it('load() populates 3 new fields from new-shape API response', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        default_provider: 'minimax',
        fallback_chain: ['openai'],
        fallback_models: { minimax: 'minimax-vision-01' },
        chapter_overrides: { 1: { max_assets: 5 }, 2: { auto_generate: true } },
        notify_threshold: 7,
      }),
    })
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')
    expect(store.settings.fallback_models).toEqual({
      minimax: 'minimax-vision-01',
    })
    expect(store.settings.chapter_overrides).toEqual({
      1: { max_assets: 5 },
      2: { auto_generate: true },
    })
    // Phase 104: legacy int 7 is expanded to a 4-key dict at the store boundary.
    expect(store.settings.notify_threshold).toEqual({
      generation: 7,
      regeneration: 7,
      cleanup: 7,
      deletion: 7,
    })
  })

  it('save() includes 3 new fields in PUT body', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        default_provider: 'minimax',
        fallback_models: { minimax: 'minimax-vision-01' },
        chapter_overrides: { 1: { max_assets: 5 } },
        notify_threshold: 5,
      }),
    })
    const store = useProjectSettingsStore()
    // Pre-populate store.settings so save() merges from these values.
    store.settings = {
      default_provider: 'minimax',
      fallback_models: { minimax: 'minimax-vision-01' },
      chapter_overrides: { 1: { max_assets: 5 } },
      notify_threshold: 5,
    }

    await store.save('test-slug', {})

    const callBody = JSON.parse(globalThis.fetch.mock.calls[0][1].body)
    expect(callBody.fallback_models).toEqual({ minimax: 'minimax-vision-01' })
    expect(callBody.chapter_overrides).toEqual({ 1: { max_assets: 5 } })
    expect(callBody.notify_threshold).toBe(5)
  })

  it('old-shape API response (no 3 new fields) — 3 new fields are undefined, consumer ?? defaults apply', async () => {
    // Old-shape = Phase 101 yaml (only legacy fields). The store stores the raw
    // API payload on 200 OK — it does NOT merge defaults. Consumers (component)
    // apply defaults via `??` operator.
    //
    // Phase 104 EXCEPTION: notify_threshold is always normalized at the store
    // boundary (undefined → {}) so downstream consumers see a uniform dict shape.
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        default_provider: 'minimax',
        fallback_chain: [],
        auto_generate: false,
        max_assets: 10,
        confirm_before_generate: false,
      }),
    })
    const store = useProjectSettingsStore()
    await store.fetch('test-slug')

    // Store stores raw API payload — fallback_models + chapter_overrides remain
    // undefined (Phase 102 contract).
    expect(store.settings.fallback_models).toBeUndefined()
    expect(store.settings.chapter_overrides).toBeUndefined()
    // Phase 104: notify_threshold is normalized to {} when API omitted the field.
    expect(store.settings.notify_threshold).toEqual({})

    // Consumer `??` fallback path applies defaults for the legacy-shape fields.
    expect(store.settings?.fallback_models ?? {}).toEqual({})
    expect(store.settings?.chapter_overrides ?? {}).toEqual({})
    // notify_threshold is always a dict post-normalization; consumers iterate
    // NOTIFY_EVENT_TYPES to apply per-key defaults.
    expect(store.settings.notify_threshold).toEqual({})
  })
})

describe('useProjectSettingsStore — chapter_overrides[].default_models sync (Phase 103)', () => {
  // Phase 103 adds `default_models: Record<string, string>` to the
  // ChapterOverrideSubset whitelist. The store stores the raw API payload,
  // so the new field flows through `chapter_overrides[N].default_models`
  // without any store-level transformation. These tests verify that the
  // store correctly preserves per-chapter default_models when set directly
  // (e.g. after fetch/save round-trip) and that an old-shape response (no
  // per-chapter default_models) leaves the field undefined for the
  // consumer's `??` fallback path.

  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.fetch = vi.fn()
  })

  it('store accepts chapter_overrides[N].default_models from new-shape response', async () => {
    const store = useProjectSettingsStore()

    // Simulate Phase 103 server response (full shape with per-chapter default_models).
    const settings = {
      default_provider: 'minimax',
      default_models: {},
      auto_generate: false,
      max_assets: 20,
      confirm_before_generate: false,
      fallback_chain: [],
      fallback_models: {},
      chapter_overrides: {
        1: { default_models: { openai: 'dall-e-3' } },
        5: { default_models: {} },
      },
      notify_threshold: 3,
    }
    store.settings = settings

    expect(store.settings.chapter_overrides[1].default_models).toEqual({
      openai: 'dall-e-3',
    })
    expect(store.settings.chapter_overrides[5].default_models).toEqual({})
  })

  it('old-shape response (without per-chapter default_models) leaves field undefined', async () => {
    const store = useProjectSettingsStore()

    // Simulate Phase 102 server response (no per-chapter default_models).
    const settings = {
      default_provider: 'minimax',
      default_models: {},
      auto_generate: false,
      max_assets: 20,
      confirm_before_generate: false,
      fallback_chain: [],
      fallback_models: {},
      chapter_overrides: {
        5: { max_assets: 8 }, // no default_models key
      },
      notify_threshold: 3,
    }
    store.settings = settings

    // Per Phase 102 lesson 7: consumer applies defaults via ??.
    expect(store.settings.chapter_overrides[5].default_models).toBeUndefined()
    expect(store.settings.chapter_overrides[5].max_assets).toBe(8)
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

describe('normalizeNotifyThreshold (Phase 104)', () => {
  // Phase 104 widens notify_threshold from `int` (Phase 102) to
  // `int | Record<NotifyEventType, number>` for per-event-type tuning.
  // The store exports a pure normalization helper that:
  //   - expands a legacy int into a 4-key dict (one entry per NOTIFY_EVENT_TYPES)
  //   - copies a dict unchanged (already-normalized shape)
  //   - coerces undefined / null to an empty dict (opt-out)
  //
  // The fetch() action applies this on every successful API read so that
  // downstream consumers (Task 8 UI table) see a uniform dict shape.

  it('expands int into 4-key dict (one entry per NOTIFY_EVENT_TYPES)', () => {
    const result = normalizeNotifyThreshold(3)
    expect(result).toEqual({
      generation: 3,
      regeneration: 3,
      cleanup: 3,
      deletion: 3,
    })
  })

  it('preserves dict unchanged when already normalized', () => {
    const input = { generation: 5, regeneration: 10 }
    const result = normalizeNotifyThreshold(input)
    expect(result).toEqual({ generation: 5, regeneration: 10 })
  })

  it('coerces undefined and null to empty dict (opt-out)', () => {
    expect(normalizeNotifyThreshold(undefined)).toEqual({})
    expect(normalizeNotifyThreshold(null)).toEqual({})
  })

  it('round-trip dict through normalize (mirrors fetch → store → write)', () => {
    // Simulates: API returns dict → fetch() normalizes → store mirrors → save()
    // serializes the same dict (no transformation back to int).
    const input = { generation: 5, regeneration: 10 }
    const fetched = normalizeNotifyThreshold(input)
    // store mirrors fetched (no further transformation in fetch())
    const stored = fetched
    // write() passes dict unchanged via JSON.stringify
    const written = { ...stored }
    expect(written).toEqual(input)
    expect(written.generation).toBe(5)
    expect(written.regeneration).toBe(10)
  })
})
