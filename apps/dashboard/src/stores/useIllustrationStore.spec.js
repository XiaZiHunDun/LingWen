import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIllustrationStore } from './useIllustrationStore.js'

// Phase 97 Task 11 — multipart vs JSON dispatch in useIllustrationStore.generate.
// When params.per_call_reference is a File, send multipart/form-data so the
// backend can read the per-call override via UploadFile. Otherwise stay on
// JSON (Phase 96 path) with use_project_reference boolean.
describe('useIllustrationStore.generate — multipart dispatch (Phase 97)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn()
  })

  it('uses FormData when per_call_reference is File', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({ id: 'fake', type: 'chapter' })

    const file = new File(['x'], 'ref.jpg', { type: 'image/jpeg' })
    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: false,
      per_call_reference: file,
    })

    const callArgs = globalThis.$fetch.mock.calls[0]
    expect(callArgs[0]).toBe('/api/illustrations/generate')
    expect(callArgs[1].method).toBe('POST')
    const body = callArgs[1].body
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('file')).toBe(file)
    expect(body.get('use_project_reference')).toBe('false')
  })

  it('uses JSON when no per_call_reference', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({ id: 'fake', type: 'chapter' })

    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: true,
    })

    const callArgs = globalThis.$fetch.mock.calls[0]
    expect(typeof callArgs[1].body).toBe('object')
    expect(callArgs[1].body.use_project_reference).toBe(true)
  })

  it('strips per_call_reference from JSON path', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({ id: 'fake', type: 'chapter' })

    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: true,
      per_call_reference: undefined,
    })

    const body = globalThis.$fetch.mock.calls[0][1].body
    expect(body.per_call_reference).toBeUndefined()
  })
})

// Phase 107: useIllustrationStore.bulkDeleteAssets — reactive local removal
// of deleted + not_found assets. Lazy-imports api/illustrations.
describe('useIllustrationStore.bulkDeleteAssets — Phase 107', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn()
    // Reset module registry so vi.mock from prior describe doesn't leak.
    vi.resetModules()
  })

  it('BulkHappy: removes deleted assets from local state and returns result', async () => {
    // Lazy-import the store fresh inside the test so vi.mock takes effect.
    vi.doMock('@/api/illustrations', () => ({
      bulkDeleteAssets: vi.fn().mockResolvedValue({
        deleted: ['a'],
        failed: [],
        summary: { total: 1, ok: 1, fail: 0 },
      }),
    }))
    const { useIllustrationStore: freshStore } = await import('./useIllustrationStore.js')
    const store = freshStore()
    store.assets = [
      { id: 'a', type: 'chapter', chapter_num: 1 },
      { id: 'b', type: 'chapter', chapter_num: 1 },
    ]

    const result = await store.bulkDeleteAssets('test-slug', ['a'])
    expect(result.deleted).toEqual(['a'])
    expect(store.assets.map(a => a.id)).toEqual(['b'])
  })

  it('BulkPartial: keeps store_error failures in local state; removes not_found', async () => {
    vi.doMock('@/api/illustrations', () => ({
      bulkDeleteAssets: vi.fn().mockResolvedValue({
        deleted: ['a'],
        failed: [
          { id: 'b', status: 'store_error' },
          { id: 'c', status: 'not_found' },
        ],
        summary: { total: 3, ok: 1, fail: 2 },
      }),
    }))
    const { useIllustrationStore: freshStore } = await import('./useIllustrationStore.js')
    const store = freshStore()
    store.assets = [
      { id: 'a', type: 'chapter', chapter_num: 1 },
      { id: 'b', type: 'chapter', chapter_num: 1 },
      { id: 'c', type: 'chapter', chapter_num: 1 },
    ]

    await store.bulkDeleteAssets('test-slug', ['a', 'b', 'c'])
    // store_error failure stays (may retry); not_found is removed (asset gone)
    expect(store.assets.map(a => a.id)).toEqual(['b'])
  })
})

// Phase 108: useIllustrationStore.bulkRegenerateAssets — reactive local update
// of each regenerated entry by id (atomic scene_json + url swap). Lazy-imports
// api/illustrations. stage_error + unknown_model retained for retry; not_found
// removed defensively.
describe('useIllustrationStore.bulkRegenerateAssets — Phase 108', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn()
    // Reset module registry so vi.mock from prior describe doesn't leak.
    vi.resetModules()
  })

  it('BulkRegenHappy: updates each regenerated entry in local state and returns result', async () => {
    vi.doMock('@/api/illustrations', () => ({
      bulkRegenerateAssets: vi.fn().mockResolvedValue({
        regenerated: [
          { id: 'a', scene_json: { new: 'a' }, url: '/new/a' },
          { id: 'b', scene_json: { new: 'b' }, url: '/new/b' },
          { id: 'c', scene_json: { new: 'c' }, url: '/new/c' },
        ],
        failed: [],
        summary: { total: 3, ok: 3, fail: 0 },
      }),
    }))
    const { useIllustrationStore: freshStore } = await import('./useIllustrationStore.js')
    const store = freshStore()
    store.assets = [
      { id: 'a', scene_json: { old: 'a' }, url: '/old/a' },
      { id: 'b', scene_json: { old: 'b' }, url: '/old/b' },
      { id: 'c', scene_json: { old: 'c' }, url: '/old/c' },
    ]

    const result = await store.bulkRegenerateAssets('test-slug', ['a', 'b', 'c'])
    expect(result.summary.ok).toBe(3)
    expect(store.assets.find(a => a.id === 'a').scene_json).toEqual({ new: 'a' })
    expect(store.assets.find(a => a.id === 'b').url).toBe('/new/b')
  })

  it('BulkRegenPartial: retains stage_error for retry; removes not_found; updates ok', async () => {
    vi.doMock('@/api/illustrations', () => ({
      bulkRegenerateAssets: vi.fn().mockResolvedValue({
        regenerated: [
          { id: 'a', scene_json: { new: 'a' }, url: '/new/a' },
        ],
        failed: [
          { id: 'b', status: 'stage_error', stage: 'stage_3' },
          { id: 'c', status: 'not_found' },
        ],
        summary: { total: 3, ok: 1, fail: 2 },
      }),
    }))
    const { useIllustrationStore: freshStore } = await import('./useIllustrationStore.js')
    const store = freshStore()
    store.assets = [
      { id: 'a', scene_json: { old: 'a' }, url: '/old/a' },
      { id: 'b', scene_json: { old: 'b' }, url: '/old/b' },
      { id: 'c', scene_json: { old: 'c' }, url: '/old/c' },
    ]

    await store.bulkRegenerateAssets('test-slug', ['a', 'b', 'c'])
    // 'a' updated to new server content
    expect(store.assets.find(a => a.id === 'a').scene_json).toEqual({ new: 'a' })
    // 'b' stage_error retained with original scene_json (retry candidate)
    expect(store.assets.find(a => a.id === 'b').scene_json).toEqual({ old: 'b' })
    // 'c' not_found removed (asset gone)
    expect(store.assets.find(a => a.id === 'c')).toBeUndefined()
  })
})
