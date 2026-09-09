// tests/unit/write-workspace-conflict-resolution.spec.ts — Phase 41
// Conflict resolution helpers: clearLocalEdits, buildLocalMarkdown, triggerDownload.

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'

import {
  clearLocalEdits,
  buildLocalMarkdown,
  triggerDownload,
} from '@/utils/writeWorkspace/conflictResolution.js'

describe('clearLocalEdits', () => {
  test('calls store.markSaved() and persist.cancel()', () => {
    const store = { markSaved: vi.fn() }
    const persist = { cancel: vi.fn() }

    clearLocalEdits({ store, persist })

    expect(store.markSaved).toHaveBeenCalledTimes(1)
    expect(persist.cancel).toHaveBeenCalledTimes(1)
  })

  test('marks saved before cancelling (so dirty flag clears even if cancel throws)', () => {
    const order: string[] = []
    const store = { markSaved: vi.fn(() => order.push('markSaved')) }
    const persist = { cancel: vi.fn(() => order.push('cancel')) }

    clearLocalEdits({ store, persist })

    expect(order).toEqual(['markSaved', 'cancel'])
  })
})

describe('buildLocalMarkdown', () => {
  test('produces YAML frontmatter + HTML body separated by blank line', () => {
    const md = buildLocalMarkdown({
      chapter: 12,
      title: '试炼之塔',
      body: '<p>正文段落一</p><p>段落二</p>',
      scenes: [],
      lastModifiedAt: '2026-09-09T10:00:00.000Z',
    })

    expect(md.startsWith('---\n')).toBe(true)
    expect(md).toContain('chapter: 12')
    expect(md).toContain('title: 试炼之塔')
    expect(md).toContain('last_modified_at: 2026-09-09T10:00:00.000Z')
    expect(md).toContain('<p>正文段落一</p><p>段落二</p>')
  })

  test('serializes scenes array as YAML list under scenes key', () => {
    const md = buildLocalMarkdown({
      chapter: 1,
      title: '开篇',
      body: '<p>x</p>',
      scenes: [
        { id: 's1', name: '开场' },
        { id: 's2', name: '转折' },
      ],
      lastModifiedAt: '2026-09-09T10:00:00.000Z',
    })

    expect(md).toMatch(/scenes:\n\s+- id: s1\n\s+name: 开场\n\s+- id: s2\n\s+name: 转折/)
  })
})

describe('triggerDownload', () => {
  let originalCreateElement: typeof document.createElement
  let originalCreateObjectURL: typeof URL.createObjectURL
  let originalRevokeObjectURL: typeof URL.revokeObjectURL
  let createObjectURLMock: ReturnType<typeof vi.fn>
  let revokeObjectURLMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    originalCreateElement = document.createElement.bind(document)
    originalCreateObjectURL = URL.createObjectURL
    originalRevokeObjectURL = URL.revokeObjectURL
    createObjectURLMock = vi.fn(() => 'blob:mock-url')
    revokeObjectURLMock = vi.fn()
    URL.createObjectURL = createObjectURLMock as unknown as typeof URL.createObjectURL
    URL.revokeObjectURL = revokeObjectURLMock as unknown as typeof URL.revokeObjectURL
  })

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL
    URL.revokeObjectURL = originalRevokeObjectURL
  })

  test('creates blob with text/markdown MIME and triggers anchor download', () => {
    const clickSpy = vi.fn()
    document.createElement = vi.fn((tag: string) => {
      const el = originalCreateElement(tag)
      if (tag === 'a') el.click = clickSpy
      return el
    }) as typeof document.createElement

    triggerDownload('ch12.local.md', '---\nchapter: 12\n---\n')

    expect(createObjectURLMock).toHaveBeenCalledTimes(1)
    const blob = createObjectURLMock.mock.calls[0][0] as Blob
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toBe('text/markdown;charset=utf-8')
    expect(clickSpy).toHaveBeenCalledTimes(1)
    expect(revokeObjectURLMock).toHaveBeenCalledWith('blob:mock-url')
  })
})