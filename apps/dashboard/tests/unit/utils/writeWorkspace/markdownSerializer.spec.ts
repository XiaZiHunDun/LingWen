// apps/dashboard/tests/unit/utils/writeWorkspace/markdownSerializer.spec.ts
import { describe, it, expect } from 'vitest'
import { parseChapterMarkdown, serializeChapterMarkdown } from '@/utils/writeWorkspace/markdownSerializer'

describe('parseChapterMarkdown', () => {
  it('extracts front-matter and body', () => {
    const md = `---
chapter: 12
title: 灰烬中的回声
scenes:
  - id: s1
    title: 雨夜
    word_count: 10
total_words: 10
last_modified_by: human
last_modified_at: 2026-08-26T00:00:00Z
---

<!--scene:s1-->
雨下得很大。`

    const result = parseChapterMarkdown(md)
    expect(result.frontmatter.chapter).toBe(12)
    expect(result.frontmatter.scenes).toHaveLength(1)
    expect(result.body).toBe('<!--scene:s1-->\n雨下得很大。')
  })

  it('throws on missing front-matter', () => {
    expect(() => parseChapterMarkdown('no frontmatter here')).toThrow(/front-matter/)
  })
})

describe('serializeChapterMarkdown', () => {
  it('round-trips with parseChapterMarkdown', () => {
    const original = `---
chapter: 12
title: 灰烬中的回声
scenes:
  - id: s1
    title: 雨夜
    word_count: 10
total_words: 10
last_modified_by: human
last_modified_at: 2026-08-26T00:00:00Z
---

<!--scene:s1-->
雨下得很大。`

    const parsed = parseChapterMarkdown(original)
    const serialized = serializeChapterMarkdown(parsed.frontmatter, parsed.body)
    expect(serialized).toBe(original)
  })

  it('emits datetime in ISO 8601 with Z suffix', () => {
    const out = serializeChapterMarkdown(
      { chapter: 1, title: 't', scenes: [], total_words: 0,
        last_modified_by: 'human', last_modified_at: '2026-08-26T00:00:00.000Z' },
      'body'
    )
    expect(out).toMatch(/last_modified_at: 2026-08-26T00:00:00Z\n/)
  })
})