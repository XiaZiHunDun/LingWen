import { useMessage } from 'naive-ui'

export interface BulkRegenerateToastResult {
  regenerated: unknown[]
  failed: Array<{ id: string; status: string }>
  summary: { total: number; ok: number; fail: number }
}

export interface BulkRegenerateToastApi {
  showResult(result: BulkRegenerateToastResult): void
  showValidationError(message: string): void
  showNetworkError(message: string): void
}

// Phase 108: encapsulates Naive UI useMessage for 3 toast variants
// covering the bulk regenerate result matrix (full success / partial / all-fail).
// Mirrors useBulkDeleteToast (Phase 107) — both bulk UX paths share the
// same 3-state toast pattern so the user sees consistent feedback.
//
// `useMessage()` is called lazily on first toast to defer the message
// provider dependency until render-time. This lets components mount
// outside an <n-message-provider> for testing — tests that never trigger
// a toast (F1-F3 selection-state tests) avoid the "no message provider"
// runtime warning. Matches the Phase 107 fixup pattern.
export function useBulkRegenerateToast(): BulkRegenerateToastApi {
  let messageInstance: ReturnType<typeof useMessage> | null = null

  function getMessage() {
    if (!messageInstance) {
      messageInstance = useMessage()
    }
    return messageInstance
  }

  return {
    showResult(result) {
      const { ok, fail } = result.summary
      const m = getMessage()
      if (fail === 0) {
        m.success(`已再生 ${ok} 张插图`)
      } else if (ok === 0) {
        m.error(`0 个成功，${fail} 个失败 — 查看详情`)
      } else {
        m.warning(`已再生 ${ok} 张，失败 ${fail} 张 — 查看详情`)
      }
    },
    showValidationError(msg: string) {
      getMessage().error(msg)
    },
    showNetworkError(msg: string) {
      getMessage().error(`网络错误：${msg}`)
    },
  }
}