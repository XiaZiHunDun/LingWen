import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useWriteWorkspacePersistence } from '@/composables/useWriteWorkspacePersistence'

describe('useWriteWorkspacePersistence', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('debounces save calls by 800ms', () => {
    const saveFn = vi.fn().mockResolvedValue({ path: 'x', mtime: 1, snapshot_path: 's' })
    const persist = useWriteWorkspacePersistence({ saveFn, debounceMs: 800 })

    persist.scheduleSave({ chapterId: 1, frontmatter: {}, body: 'a' })
    persist.scheduleSave({ chapterId: 1, frontmatter: {}, body: 'b' })
    persist.scheduleSave({ chapterId: 1, frontmatter: {}, body: 'c' })

    expect(saveFn).not.toHaveBeenCalled()
    vi.advanceTimersByTime(800)
    expect(saveFn).toHaveBeenCalledTimes(1)
    expect(saveFn.mock.calls[0][0].body).toBe('c')
  })

  it('flushNow skips debounce', async () => {
    const saveFn = vi.fn().mockResolvedValue({ path: 'x', mtime: 1, snapshot_path: 's' })
    const persist = useWriteWorkspacePersistence({ saveFn, debounceMs: 800 })
    persist.scheduleSave({ chapterId: 1, frontmatter: {}, body: 'a' })
    await persist.flushNow()
    expect(saveFn).toHaveBeenCalledTimes(1)
  })

  it('detects conflict via mtime callback', () => {
    const saveFn = vi.fn().mockResolvedValue({ path: 'x', mtime: 1, snapshot_path: 's' })
    const persist = useWriteWorkspacePersistence({ saveFn, debounceMs: 800 })
    expect(persist.detectConflict(100, 100)).toBe(false)
    expect(persist.detectConflict(100, 101)).toBe(true)
  })
})
