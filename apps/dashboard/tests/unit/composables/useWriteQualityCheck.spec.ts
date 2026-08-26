import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWriteQualityCheck } from '@/composables/useWriteQualityCheck'

describe('useWriteQualityCheck', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('POSTs chapter body and parses annotations', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        annotations: [
          { sceneId: 's1', offset: 5, severity: 'P0', rule: 'consistency:character_name', msg: '林夜 vs 林葉' },
        ],
      }),
    })
    const qc = useWriteQualityCheck()
    const result = await qc.runCheck({ chapterId: 12, body: '雨下得很大。林葉。' })
    expect(result.annotations).toHaveLength(1)
    expect(result.annotations[0].severity).toBe('P0')
    expect(global.fetch).toHaveBeenCalledWith('/api/quality/run', expect.objectContaining({ method: 'POST' }))
  })

  it('throws on error', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, statusText: 'Server Error' })
    const qc = useWriteQualityCheck()
    await expect(qc.runCheck({ chapterId: 1, body: '' })).rejects.toThrowError('Server Error')
  })
})