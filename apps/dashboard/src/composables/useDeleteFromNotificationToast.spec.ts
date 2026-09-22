import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMessage } from 'naive-ui'
import { useDeleteFromNotificationToast } from '@/composables/useDeleteFromNotificationToast'

vi.mock('naive-ui', () => ({
  useMessage: vi.fn(),
}))

describe('useDeleteFromNotificationToast', () => {
  const mockMessage = {
    success: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  }

  beforeEach(() => {
    vi.mocked(useMessage).mockReturnValue(mockMessage as any)
    vi.clearAllMocks()
  })

  it('T-success: status=deleted calls message.success', () => {
    const { showResult } = useDeleteFromNotificationToast()
    showResult({ status: 'deleted' })
    expect(mockMessage.success).toHaveBeenCalledWith('已删除资产')
    expect(mockMessage.info).not.toHaveBeenCalled()
    expect(mockMessage.error).not.toHaveBeenCalled()
  })

  it('T-not-found: status=not_found calls message.info', () => {
    const { showResult } = useDeleteFromNotificationToast()
    showResult({ status: 'not_found' })
    expect(mockMessage.info).toHaveBeenCalledWith('资产不存在或已被删除')
    expect(mockMessage.success).not.toHaveBeenCalled()
    expect(mockMessage.error).not.toHaveBeenCalled()
  })

  it('T-error: status=error calls message.error', () => {
    const { showResult } = useDeleteFromNotificationToast()
    showResult({ status: 'error', error: new Error('500') })
    expect(mockMessage.error).toHaveBeenCalledWith('删除失败')
    expect(mockMessage.success).not.toHaveBeenCalled()
    expect(mockMessage.info).not.toHaveBeenCalled()
  })
})