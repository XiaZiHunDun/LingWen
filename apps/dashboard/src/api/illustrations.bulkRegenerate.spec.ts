// Phase 108: bulk regenerate illustration endpoint typed wrapper tests
// Mirrors Phase 107 illustrations.bulkDelete.spec.ts pattern.
// Uses $fetch (Nuxt/ofetch global) — bulk regenerate spec chose $fetch over plain fetch
// (the bulk delete wrapper at lines 192-215 uses plain fetch; both work in tests
// via vi.stubGlobal). Limit is 10 (Phase 108) vs 50 (Phase 107).
import { describe, expect, it, vi, beforeEach } from 'vitest'

describe('bulkRegenerateAssets', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('T1: empty assetIds throws Error with "at least 1" message', async () => {
    const mockFetch = vi.fn()
    ;(globalThis as any).$fetch = mockFetch

    const mod = await import('./illustrations')
    await expect(mod.bulkRegenerateAssets('demo', [])).rejects.toThrow(/at least 1/)
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('T2: 11 assetIds throws Error with "at most 10" message', async () => {
    const mockFetch = vi.fn()
    ;(globalThis as any).$fetch = mockFetch

    const mod = await import('./illustrations')
    const ids = Array.from({ length: 11 }, (_, i) => `id${i}`)
    await expect(mod.bulkRegenerateAssets('demo', ids)).rejects.toThrow(/at most 10/)
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('T3: happy path 3 assets → PUT with slug=demo, ids=a%2Cb%2Cc', async () => {
    const mockFetch = vi.fn().mockResolvedValueOnce({
      regenerated: ['a', 'b', 'c'],
      failed: [],
      summary: { total: 3, ok: 3, fail: 0 },
    })
    ;(globalThis as any).$fetch = mockFetch

    const mod = await import('./illustrations')
    const result = await mod.bulkRegenerateAssets('demo', ['a', 'b', 'c'])

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('/api/illustrations?slug=demo&ids=a%2Cb%2Cc')
    expect(opts).toEqual({ method: 'PUT' })
    expect(result.summary).toEqual({ total: 3, ok: 3, fail: 0 })
  })

  it('T4: with provider/model/fallback_chain options → URL contains all 3', async () => {
    const mockFetch = vi.fn().mockResolvedValueOnce({
      regenerated: ['a'],
      failed: [],
      summary: { total: 1, ok: 1, fail: 0 },
    })
    ;(globalThis as any).$fetch = mockFetch

    const mod = await import('./illustrations')
    await mod.bulkRegenerateAssets('demo', ['a'], {
      provider: 'openai',
      model: 'dall-e-3',
      fallbackChain: 'minimax,openai',
    })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url] = mockFetch.mock.calls[0]
    // URLSearchParams encodes commas as %2C
    expect(url).toContain('provider=openai')
    expect(url).toContain('model=dall-e-3')
    expect(url).toContain('fallback_chain=minimax%2Copenai')
  })
})
