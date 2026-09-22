import { useMessage } from 'naive-ui'
import type { BulkDeleteResult } from '@/api/illustrations'

// Phase 107: encapsulates Naive UI useMessage for 3 toast variants
// covering the bulk delete result matrix (full success / partial / all-fail).
// Reusable across LibraryPage and WriteWorkspacePage — both mount
// <IllustrationGallery> which calls showBulkDeleteResult after
// confirmBulkDelete completes.
//
// The failure-list <NDrawer> with selective retry is intentionally NOT here:
// the drawer is per-page interaction (each page owns gallery state + retry
// handlers). Keeping the composable narrow (toast only) avoids coupling
// bulk UX to a single consumer's drawer layout.
export function useBulkDeleteToast() {
  const message = useMessage()

  function showBulkDeleteResult(_slug: string, result: BulkDeleteResult): void {
    const { ok, fail } = result.summary
    if (fail === 0) {
      message.success(`已删除 ${ok} 张插图`)
    } else if (ok === 0) {
      message.error(`0 个成功，${fail} 个失败 — 查看详情`)
    } else {
      message.warning(`已删除 ${ok} 张，失败 ${fail} 张 — 查看详情`)
    }
  }

  function showValidationError(detail: string): void {
    message.error(`批量删除失败：${detail}`)
  }

  return { showBulkDeleteResult, showValidationError }
}