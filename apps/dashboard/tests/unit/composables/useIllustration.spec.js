import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIllustrationStore } from '@/stores/useIllustrationStore'

describe('useIllustrationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn()
  })

  // --- initial state ---

  it('starts with empty assets list and null slug', () => {
    const store = useIllustrationStore()
    expect(store.assets).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBe(null)
    expect(store.projectSlug).toBe(null)
  })

  // --- loadAssets ---

  it('loadAssets populates store on success', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({
      assets: [{ id: 'a', type: 'chapter', chapter_num: 17, style_preset: 'ink' }],
    })

    await store.loadAssets('test-project')
    expect(store.assets).toHaveLength(1)
    expect(store.assets[0].id).toBe('a')
    expect(store.projectSlug).toBe('test-project')
    expect(store.loading).toBe(false)
  })

  it('loadAssets sets error on failure', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockRejectedValue(new Error('network'))

    await store.loadAssets('test-project')
    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })

  it('loadAssets clears stale state on project switch', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({
      assets: [{ id: 'a', type: 'chapter' }],
    })
    await store.loadAssets('project-A')
    expect(store.assets[0].id).toBe('a')

    globalThis.$fetch.mockResolvedValue({
      assets: [{ id: 'b', type: 'chapter' }],
    })
    await store.loadAssets('project-B')
    // Stale project-A data should be cleared
    expect(store.assets.map(a => a.id)).toEqual(['b'])
    expect(store.projectSlug).toBe('project-B')
  })

  // --- generate ---

  it('generate prepends the new asset to the list', async () => {
    const store = useIllustrationStore()
    // Seed with existing asset
    globalThis.$fetch.mockResolvedValueOnce({
      assets: [{ id: 'old', type: 'chapter' }],
    })
    await store.loadAssets('test')

    globalThis.$fetch.mockResolvedValueOnce({
      id: 'new', type: 'chapter', chapter_num: 18, style_preset: 'ink', scene_json: {},
    })
    const result = await store.generate('test', {
      type: 'chapter', chapter_num: 18, style_preset: 'ink', custom_prompt: null,
    })
    expect(result.id).toBe('new')
    expect(store.assets[0].id).toBe('new')
    expect(store.assets[1].id).toBe('old')
  })

  it('generate rethrows on error so caller can show retry', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockRejectedValue(new Error('API down'))

    await expect(
      store.generate('test', { type: 'chapter', chapter_num: 1, style_preset: 'ink' })
    ).rejects.toThrow('API down')
    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })

  // --- deleteAsset ---

  it('deleteAsset removes the asset from local state', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValueOnce({
      assets: [{ id: 'a', type: 'chapter' }, { id: 'b', type: 'chapter' }],
    })
    await store.loadAssets('test')

    globalThis.$fetch.mockResolvedValueOnce({ deleted: 'a' })
    await store.deleteAsset('test', 'a')
    expect(store.assets.map(x => x.id)).toEqual(['b'])
  })

  // --- regenerate ---

  it('regenerate replaces in-place via PUT (v55.4 atomic swap)', async () => {
    const store = useIllustrationStore()
    // Seed
    globalThis.$fetch.mockResolvedValueOnce({
      assets: [{ id: 'old', type: 'chapter', chapter_num: 17, style_preset: 'ink', custom_prompt: null }],
    })
    await store.loadAssets('test')

    // Phase 94: PUT /{id}/regenerate preserves asset_id and atomically swaps
    // bytes via temp file + POSIX rename on the backend. v1 DELETE+POST is gone.
    globalThis.$fetch.mockResolvedValueOnce({
      id: 'old', type: 'chapter', chapter_num: 17, style_preset: 'ink', custom_prompt: null, scene_json: {},
    })
    const result = await store.regenerate('test', 'old')
    expect(result.id).toBe('old')
    expect(store.assets.map(x => x.id)).toEqual(['old'])
    expect(globalThis.$fetch).toHaveBeenCalledTimes(2)  // loadAssets + PUT regenerate
  })

  it('regenerate defensively prepends when asset not in local cache', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValueOnce({
      id: 'new', type: 'chapter', chapter_num: 17, style_preset: 'ink', custom_prompt: null, scene_json: {},
    })
    const result = await store.regenerate('test', 'missing-id')
    expect(result.id).toBe('new')
    expect(store.assets.map(x => x.id)).toEqual(['new'])
  })

  // --- composable wrapper ---

  it('useIllustration composable returns project-scoped helpers', async () => {
    const { useIllustration } = await import('@/composables/useIllustration')
    globalThis.$fetch.mockResolvedValueOnce({
      assets: [
        { id: 'c1', type: 'chapter', chapter_num: 1 },
        { id: 'c2', type: 'chapter', chapter_num: 2 },
        { id: 'cover1', type: 'cover' },
      ],
    })
    const { chapterAssets, coverAssets, getForChapter } = useIllustration('test')
    await useIllustration('test').loadAssets()
    expect(chapterAssets.value.map(a => a.id)).toEqual(['c1', 'c2'])
    expect(coverAssets.value.map(a => a.id)).toEqual(['cover1'])
    expect(getForChapter(2).id).toBe('c2')
    expect(getForChapter(99)).toBeUndefined()
  })
})
