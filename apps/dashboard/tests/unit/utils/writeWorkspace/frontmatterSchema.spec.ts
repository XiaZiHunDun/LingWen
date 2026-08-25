// apps/dashboard/tests/unit/utils/writeWorkspace/frontmatterSchema.spec.ts
import { describe, it, expect } from 'vitest'
import { ChapterFrontmatterSchema, SceneMetaSchema } from '../../../../src/utils/writeWorkspace/frontmatterSchema.js'

describe('ChapterFrontmatterSchema', () => {
  it('rejects missing chapter number', () => {
    const result = ChapterFrontmatterSchema.safeParse({
      title: '灰烬中的回声',
      scenes: [],
      total_words: 0,
      last_modified_by: 'human',
      last_modified_at: '2026-08-26T00:00:00Z',
    })
    expect(result.success).toBe(false)
  })

  it('accepts a valid chapter frontmatter', () => {
    const result = ChapterFrontmatterSchema.safeParse({
      chapter: 12,
      title: '灰烬中的回声',
      scenes: [{ id: 's1', title: '雨夜', word_count: 412 }],
      total_words: 2830,
      last_modified_by: 'human',
      last_modified_at: '2026-08-26T00:00:00Z',
    })
    expect(result.success).toBe(true)
  })

  it('rejects last_modified_by other than human|agent', () => {
    const result = ChapterFrontmatterSchema.safeParse({
      chapter: 12, title: 'x', scenes: [], total_words: 0,
      last_modified_by: 'alien', last_modified_at: '2026-08-26T00:00:00Z',
    })
    expect(result.success).toBe(false)
  })
})

describe('SceneMetaSchema', () => {
  it('requires id and title', () => {
    expect(SceneMetaSchema.safeParse({ id: 's1', title: '雨夜', word_count: 100 }).success).toBe(true)
    expect(SceneMetaSchema.safeParse({ id: 's1' }).success).toBe(false)
  })
})