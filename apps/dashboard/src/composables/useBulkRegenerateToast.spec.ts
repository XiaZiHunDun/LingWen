import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMessage } from 'naive-ui'
import { useBulkRegenerateToast } from '@/composables/useBulkRegenerateToast'

vi.mock('naive-ui', () => ({
  useMessage: vi.fn(),
}))

describe('useBulkRegenerateToast', () => {
  const mockMessage = {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  }

  beforeEach(() => {
    vi.mocked(useMessage).mockReturnValue(mockMessage as any)
    vi.clearAllMocks()
  })

  it('T-success: showResult with fail=0 calls message.success', () => {
    const { showResult } = useBulkRegenerateToast()
    showResult({
      regenerated: [{}, {}, {}, {}, {}],
      failed: [],
      summary: { total: 5, ok: 5, fail: 0 },
    })
    expect(mockMessage.success).toHaveBeenCalledWith('已再生 5 张插图')
    expect(mockMessage.warning).not.toHaveBeenCalled()
    expect(mockMessage.error).not.toHaveBeenCalled()
  })

  it('T-partial: showResult with both ok and fail calls message.warning', () => {
    const { showResult } = useBulkRegenerateToast()
    showResult({
      regenerated: [{}, {}, {}],
      failed: [
        { id: 'b', status: 'stage_error' },
        { id: 'c', status: 'stage_error' },
      ],
      summary: { total: 5, ok: 3, fail: 2 },
    })
    expect(mockMessage.warning).toHaveBeenCalledWith('已再生 3 张，失败 2 张 — 查看详情')
  })

  it('T-all-fail: showResult with ok=0 calls message.error', () => {
    const { showResult } = useBulkRegenerateToast()
    showResult({
      regenerated: [],
      failed: [
        { id: 'a', status: 'stage_error' },
        { id: 'b', status: 'stage_error' },
        { id: 'c', status: 'stage_error' },
        { id: 'd', status: 'stage_error' },
        { id: 'e', status: 'stage_error' },
      ],
      summary: { total: 5, ok: 0, fail: 5 },
    })
    expect(mockMessage.error).toHaveBeenCalledWith('0 个成功，5 个失败 — 查看详情')
  })
})