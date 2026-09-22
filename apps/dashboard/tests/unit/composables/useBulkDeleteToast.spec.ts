import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMessage } from 'naive-ui'
import { useBulkDeleteToast } from '@/composables/useBulkDeleteToast'

vi.mock('naive-ui', () => ({
  useMessage: vi.fn(),
}))

describe('useBulkDeleteToast', () => {
  const mockMessage = {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  }

  beforeEach(() => {
    vi.mocked(useMessage).mockReturnValue(mockMessage as any)
    vi.clearAllMocks()
  })

  it('T-success: showBulkDeleteResult with fail=0 calls message.success', () => {
    const { showBulkDeleteResult } = useBulkDeleteToast()
    showBulkDeleteResult('slug', {
      deleted: ['a', 'b', 'c'],
      failed: [],
      summary: { total: 3, ok: 3, fail: 0 },
    })
    expect(mockMessage.success).toHaveBeenCalledWith('已删除 3 张插图')
    expect(mockMessage.warning).not.toHaveBeenCalled()
    expect(mockMessage.error).not.toHaveBeenCalled()
  })

  it('T-partial: showBulkDeleteResult with both ok and fail calls message.warning', () => {
    const { showBulkDeleteResult } = useBulkDeleteToast()
    showBulkDeleteResult('slug', {
      deleted: ['a'],
      failed: [
        { id: 'b', status: 'store_error' },
        { id: 'c', status: 'not_found' },
      ],
      summary: { total: 3, ok: 1, fail: 2 },
    })
    expect(mockMessage.warning).toHaveBeenCalledWith('已删除 1 张，失败 2 张 — 查看详情')
  })

  it('T-all-fail: showBulkDeleteResult with ok=0 calls message.error', () => {
    const { showBulkDeleteResult } = useBulkDeleteToast()
    showBulkDeleteResult('slug', {
      deleted: [],
      failed: [{ id: 'a', status: 'store_error' }],
      summary: { total: 1, ok: 0, fail: 1 },
    })
    expect(mockMessage.error).toHaveBeenCalledWith('0 个成功，1 个失败 — 查看详情')
  })
})