import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIllustrationStore } from './useIllustrationStore.js'

// Phase 97 Task 11 — multipart vs JSON dispatch in useIllustrationStore.generate.
// When params.per_call_reference is a File, send multipart/form-data so the
// backend can read the per-call override via UploadFile. Otherwise stay on
// JSON (Phase 96 path) with use_project_reference boolean.
describe('useIllustrationStore.generate — multipart dispatch (Phase 97)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn()
  })

  it('uses FormData when per_call_reference is File', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({ id: 'fake', type: 'chapter' })

    const file = new File(['x'], 'ref.jpg', { type: 'image/jpeg' })
    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: false,
      per_call_reference: file,
    })

    const callArgs = globalThis.$fetch.mock.calls[0]
    expect(callArgs[0]).toBe('/api/illustrations/generate')
    expect(callArgs[1].method).toBe('POST')
    const body = callArgs[1].body
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('file')).toBe(file)
    expect(body.get('use_project_reference')).toBe('false')
  })

  it('uses JSON when no per_call_reference', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({ id: 'fake', type: 'chapter' })

    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: true,
    })

    const callArgs = globalThis.$fetch.mock.calls[0]
    expect(typeof callArgs[1].body).toBe('object')
    expect(callArgs[1].body.use_project_reference).toBe(true)
  })

  it('strips per_call_reference from JSON path', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch.mockResolvedValue({ id: 'fake', type: 'chapter' })

    await store.generate('test-slug', {
      type: 'chapter',
      chapter_num: 1,
      style_preset: 'ink',
      custom_prompt: null,
      provider: 'minimax',
      use_project_reference: true,
      per_call_reference: undefined,
    })

    const body = globalThis.$fetch.mock.calls[0][1].body
    expect(body.per_call_reference).toBeUndefined()
  })
})
