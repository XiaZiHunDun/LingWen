/**
 * useWorkflowSocket.spec.js — Phase 9.17: MAX_HANDLERS guard test (T2).
 *
 * Spec: 2026-06-11-phase9.17-pydantic-cascade-payload-design.md (commit 8216ebe).
 * Plan: 2026-06-11-phase9.17-pydantic-cascade-payload.md.
 *
 * T2 目标: onCascadeUpdate() Set 加 MAX_HANDLERS=50 guard, 反复 mount/unmount
 * 或脚本 bug 触发累积 leak 时 console.warn + early return.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

describe('useWorkflowSocket: MAX_HANDLERS guard (Phase 9.17)', () => {
  let warnSpy

  beforeEach(() => {
    // Reset module-level singleton state via resetModules + re-import
    vi.resetModules()
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    warnSpy.mockRestore()
  })

  it('refuses to register beyond MAX_HANDLERS=50', async () => {
    const { onCascadeUpdate } = await import('../../src/composables/useWorkflowSocket.js')
    // 50 handlers register OK (Vue onBeforeUnmount warnings 50x 是 0 relevant —
    // Phase 9.16 既有 1:1 pattern, 跟 MAX_HANDLERS guard 无关)
    const handlers = Array.from({ length: 50 }, () => () => {})
    handlers.forEach((h) => onCascadeUpdate(h))
    // Reset spy to isolate MAX_HANDLERS warning from Vue warnings
    warnSpy.mockClear()
    // 51st refused → MAX_HANDLERS warning (only fires when guard present)
    const extra = () => {}
    onCascadeUpdate(extra)
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('MAX_HANDLERS=50')
    )
  })
})
