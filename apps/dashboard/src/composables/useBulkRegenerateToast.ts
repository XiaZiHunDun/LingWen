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
export function useBulkRegenerateToast(): BulkRegenerateToastApi {
  const message = useMessage()
  return {
    showResult(result) {
      const { ok, fail } = result.summary
      if (fail === 0) {
        message.success(`已再生 ${ok} 张插图`)
      } else if (ok === 0) {
        message.error(`0 个成功，${fail} 个失败 — 查看详情`)
      } else {
        message.warning(`已再生 ${ok} 张，失败 ${fail} 张 — 查看详情`)
      }
    },
    showValidationError(msg: string) {
      message.error(msg)
    },
    showNetworkError(msg: string) {
      message.error(`网络错误：${msg}`)
    },
  }
}