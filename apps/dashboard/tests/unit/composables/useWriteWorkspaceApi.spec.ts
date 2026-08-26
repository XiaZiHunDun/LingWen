import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWriteWorkspaceApi } from '@/composables/useWriteWorkspaceApi'

describe('useWriteWorkspaceApi', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('PUTs chapter with frontmatter and body', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ path: 'ch012.md', mtime: 1234567890, snapshot_path: 'snap.md' }),
    })
    const api = useWriteWorkspaceApi()
    const result = await api.saveChapter({
      chapterId: 12,
      frontmatter: { chapter: 12, title: 't', scenes: [], total_words: 0, last_modified_by: 'human', last_modified_at: '2026-08-26T00:00:00Z' },
      body: 'content',
    })
    expect(result.path).toBe('ch012.md')
    expect(global.fetch).toHaveBeenCalledWith('/api/write/12', expect.objectContaining({ method: 'PUT' }))
  })

  it('throws on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, statusText: 'Bad Request' })
    const api = useWriteWorkspaceApi()
    await expect(api.saveChapter({ chapterId: 1, frontmatter: {} as any, body: '' })).rejects.toThrowError('Save failed: Bad Request')
  })
})