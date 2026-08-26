import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useWorldAgent } from '@/composables/world/useWorldAgent.js'

describe('useWorldAgent', () => {
  const originalFetch = globalThis.fetch
  let fetchMock

  beforeEach(() => {
    fetchMock = vi.fn()
    globalThis.fetch = fetchMock
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('extractFromChapters POSTs to /api/world/agent/extract-from-chapters with correct body', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      statusText: 'OK',
      json: async () => ({ proposals_created: 2, ids: [11, 12] }),
    })

    const { extractFromChapters } = useWorldAgent()
    const result = await extractFromChapters(
      'lin-ye',
      { start: 1, end: 5 },
      ['第一章内容', '第二章内容'],
    )

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/world/agent/extract-from-chapters')
    expect(init.method).toBe('POST')
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(JSON.parse(init.body)).toEqual({
      character_slug: 'lin-ye',
      chapter_texts: ['第一章内容', '第二章内容'],
    })
    expect(result).toEqual({
      proposals_created: 2,
      ids: [11, 12],
      message: 'extracted 2 proposal(s) from chapters 1-5',
    })
  })

  it('extractFromChapters returns a friendly message on HTTP 429', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 429,
      statusText: 'Too Many Requests',
      json: async () => ({ detail: 'agent extraction rate limit exceeded' }),
    })

    const { extractFromChapters } = useWorldAgent()
    const result = await extractFromChapters('lin-ye', { start: 1, end: 1 }, [])

    expect(result.proposals_created).toBe(0)
    expect(result.ids).toEqual([])
    expect(result.message).toContain('rate limit')
  })

  it('extractFromPrompt POSTs to /api/world/agent/extract-from-prompt', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      statusText: 'OK',
      json: async () => ({ proposals_created: 1, ids: [42] }),
    })

    const { extractFromPrompt } = useWorldAgent()
    const result = await extractFromPrompt('mo-yan', '莫言在第三卷末死了')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/world/agent/extract-from-prompt')
    expect(JSON.parse(init.body)).toEqual({
      character_slug: 'mo-yan',
      prompt: '莫言在第三卷末死了',
    })
    expect(result.proposals_created).toBe(1)
    expect(result.ids).toEqual([42])
  })

  it('returns a network-error message when fetch throws', async () => {
    fetchMock.mockRejectedValue(new Error('connection refused'))

    const { extractFromChapters } = useWorldAgent()
    const result = await extractFromChapters('lin-ye', { start: 1, end: 1 }, ['x'])

    expect(result.proposals_created).toBe(0)
    expect(result.ids).toEqual([])
    expect(result.message).toContain('connection refused')
  })

  it('extractFromChapters defaults chapterTexts to []', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      statusText: 'OK',
      json: async () => ({ proposals_created: 0, ids: [] }),
    })

    const { extractFromChapters } = useWorldAgent()
    await extractFromChapters('lin-ye', { start: 1, end: 5 })

    const [, init] = fetchMock.mock.calls[0]
    expect(JSON.parse(init.body).chapter_texts).toEqual([])
  })
})