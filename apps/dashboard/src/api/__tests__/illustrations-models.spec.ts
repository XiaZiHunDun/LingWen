import { describe, expect, it, vi, beforeEach } from 'vitest'

describe('fetchProviderModels', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('returns provider model catalog with default', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      provider: 'openai',
      models: ['dall-e-3', 'dall-e-3-hd', 'dall-e-2', 'gpt-image-1'],
      default_model: 'dall-e-3',
    })
    vi.stubGlobal('fetch', fetchMock)

    const mod = await import('../illustrations')
    const result = await mod.fetchProviderModels('openai')

    expect(result.provider).toBe('openai')
    expect(result.models).toEqual(['dall-e-3', 'dall-e-3-hd', 'dall-e-2', 'gpt-image-1'])
    expect(result.default_model).toBe('dall-e-3')
    expect(fetchMock).toHaveBeenCalledWith('/api/illustrations/providers/openai/models')

    vi.unstubAllGlobals()
  })
})