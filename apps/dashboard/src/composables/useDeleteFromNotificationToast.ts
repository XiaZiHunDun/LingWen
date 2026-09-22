import { useMessage } from 'naive-ui'

// Phase 109: single-delete toast dispatcher for NotificationListItem.
// Mirrors useBulkDeleteToast pattern (Phase 107) — lazy useMessage
// so callers don't need to mount <n-message-provider> at test time.
// Maps the {status: ...} returned by useNotificationStore.deleteAssetFromNotification
// to a Naive UI toast variant.
//
// `useMessage()` is called lazily on first toast to defer the message
// provider dependency until render-time. This lets components mount
// outside an <n-message-provider> for testing — tests that never trigger
// a toast avoid the "no message provider" runtime warning.

export type DeleteFromNotificationStatus = 'deleted' | 'not_found' | 'error'

export interface DeleteFromNotificationResult {
  status: DeleteFromNotificationStatus
  error?: unknown
}

export function useDeleteFromNotificationToast() {
  let messageInstance: ReturnType<typeof useMessage> | null = null

  function getMessage() {
    if (!messageInstance) {
      messageInstance = useMessage()
    }
    return messageInstance
  }

  function showResult(result: DeleteFromNotificationResult): void {
    const m = getMessage()
    if (result.status === 'deleted') {
      m.success('已删除资产')
    } else if (result.status === 'not_found') {
      m.info('资产不存在或已被删除')
    } else {
      m.error('删除失败')
    }
  }

  return { showResult }
}