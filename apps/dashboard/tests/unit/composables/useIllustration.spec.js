import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIllustrationStore } from '@/stores/useIllustrationStore'

describe('useIllustrationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts with empty assets list', () => {
    const store = useIllustrationStore()
    expect(store.assets).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBe(null)
  })

  it('loadAssets populates store on success', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch = vi.fn().mockResolvedValue({
      assets: [{ id: 'a', type: 'chapter', chapter_num: 17, style_preset: 'ink' }],
    })

    await store.loadAssets('test-project')
    expect(store.assets).toHaveLength(1)
    expect(store.assets[0].id).toBe('a')
  })

  it('loadAssets sets error on failure', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch = vi.fn().mockRejectedValue(new Error('network'))

    await store.loadAssets('test-project')
    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })
})
