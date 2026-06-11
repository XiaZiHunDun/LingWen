// tests/unit/chapter-decision-link.spec.js — Phase 9.83 F75
import { describe, test, expect } from 'vitest'
import {
  extractChapterFromDecision,
  findPendingDecisionForChapter,
  chapterDecisionLinkEnabled,
  resolveFocusedDecisionId,
} from '../../src/utils/chapterDecisionLink.js'

describe('chapterDecisionLink (F75)', () => {
  test('extractChapterFromDecision reads context.chapter_num', () => {
    expect(extractChapterFromDecision({ context: { chapter_num: 5 } })).toBe(5)
  })

  test('findPendingDecisionForChapter by context', () => {
    const pending = [
      { decision_id: 'd1', status: 'pending', context: { chapter_num: 5 } },
    ]
    const hit = findPendingDecisionForChapter(5, pending, null)
    expect(hit?.decision_id).toBe('d1')
  })

  test('findPendingDecisionForChapter via paused production_summary', () => {
    const pending = [{ decision_id: 'd2', status: 'pending', context: {} }]
    const status = {
      paused: true,
      production_summary: { chapter_num: 7 },
    }
    expect(chapterDecisionLinkEnabled(7, pending, status)).toBe(true)
  })

  test('resolveFocusedDecisionId prefers explicit id', () => {
    const id = resolveFocusedDecisionId(5, 'd9', [
      { decision_id: 'd9', status: 'pending', context: { chapter_num: 5 } },
    ])
    expect(id).toBe('d9')
  })
})
