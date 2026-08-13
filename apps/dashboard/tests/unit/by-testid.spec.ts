// tests/unit/by-testid.spec.ts — Phase 8.35
// byTestid helper: byTestid('x') 返 '[data-testid="x"]' string
// (主公决策 Option A 2026-06-08: simple string, 0 返 object wrapper).

import { describe, test, expect } from 'vitest'
import { byTestid } from '../helpers/by-testid'

describe('byTestid helper', () => {
  test('returns [data-testid="x"] string for single token', () => {
    expect(byTestid('zoom-in-btn')).toBe('[data-testid="zoom-in-btn"]')
  })

  test('handles kebab-case multi-token ids', () => {
    expect(byTestid('workflow-node-status-running')).toBe(
      '[data-testid="workflow-node-status-running"]',
    )
  })

  test('returns same string when called twice (idempotent)', () => {
    const a = byTestid('x')
    const b = byTestid('x')
    expect(a).toBe(b)
  })

  test('does not escape special characters in id (raw passthrough)', () => {
    expect(byTestid('has-dash_and_underscore')).toBe(
      '[data-testid="has-dash_and_underscore"]',
    )
  })
})
