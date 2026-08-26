import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWriteWorkspaceStore } from '@/stores/useWriteWorkspaceStore'

describe('useWriteWorkspaceStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('starts in author mode with empty state', () => {
    const store = useWriteWorkspaceStore()
    expect(store.mode).toBe('author')
    expect(store.chapterId).toBeNull()
    expect(store.outline).toEqual([])
    expect(store.scenes).toEqual([])
    expect(store.aiDrawerOpen).toBe(false)
  })

  it('toggleMode switches author <-> editor', () => {
    const store = useWriteWorkspaceStore()
    store.toggleMode()
    expect(store.mode).toBe('editor')
    store.toggleMode()
    expect(store.mode).toBe('author')
  })

  it('load populates state from frontmatter + body', () => {
    const store = useWriteWorkspaceStore()
    store.load({
      chapterId: 12,
      frontmatter: {
        chapter: 12, title: '灰烬中的回声',
        scenes: [{ id: 's1', title: '雨夜', word_count: 412 }],
        total_words: 2830, last_modified_by: 'human',
        last_modified_at: '2026-08-26T00:00:00Z',
      },
      body: '<!--scene:s1-->\n### 雨夜\n雨下得很大。',
    })
    expect(store.chapterId).toBe(12)
    expect(store.outline).toHaveLength(1)
    expect(store.scenes[0].title).toBe('雨夜')
  })

  it('markDirty sets saveState.dirty=true and status=saving', () => {
    const store = useWriteWorkspaceStore()
    store.markDirty()
    expect(store.saveState.dirty).toBe(true)
    expect(store.saveState.status).toBe('saving')
  })

  it('markSaved clears dirty and sets lastSavedAt', () => {
    const store = useWriteWorkspaceStore()
    store.markSaved()
    expect(store.saveState.dirty).toBe(false)
    expect(store.saveState.lastSavedAt).toBeTruthy()
    expect(store.saveState.status).toBe('saved')
  })

  it('addScene appends and bumps dirty', () => {
    const store = useWriteWorkspaceStore()
    store.load({ chapterId: 1, frontmatter: { chapter: 1, title: 't', scenes: [], total_words: 0, last_modified_by: 'human', last_modified_at: '2026-08-26T00:00:00Z' }, body: '' })
    store.markSaved()
    store.addScene({ id: 's1', title: '新场景', body: '内容', wordCount: 2 })
    expect(store.scenes).toHaveLength(1)
    expect(store.saveState.dirty).toBe(true)
  })
})
