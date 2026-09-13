/**
 * Phase 63 — creationModeHint utility tests (Reading Power frontend surface).
 *
 * The Reading Power backend (packages/lingwen-reading-power/) just had its
 * 8 test files restored in Phase 57b (44/44 functional gate). The
 * frontend usage of Reading Power concepts flows through
 * `apps/dashboard/src/utils/creationModeHint.js` which exposes pure
 * helpers for mode metadata + Today hub primary-action resolution.
 *
 * This file locks the `resolveTodayPrimaryAction()` Reading Power
 * fallback case (returns "查看追读力洞察" CTA when no other priority
 * signals exist) + `creationModeMeta()` mode lookup behavior.
 *
 * Test count: 8 (3 meta + 5 action resolution).
 */

import { describe, it, expect } from 'vitest';

import {
  creationModeMeta,
  resolveTodayPrimaryAction,
} from '@/utils/creationModeHint';

// ---------------------------------------------------------------------------
// creationModeMeta
// ---------------------------------------------------------------------------

describe('creationModeMeta', () => {
  it('returns full metadata for known modes', () => {
    const companion = creationModeMeta('companion');
    expect(companion.label).toBe('陪伴模式');
    expect(companion.tagline).toContain('人主笔');
    expect(companion.audience).toContain('日常手改');

    const advance = creationModeMeta('advance');
    expect(advance.label).toBe('推进模式');
    expect(advance.tagline).toContain('脉络预警');

    const studio = creationModeMeta('studio');
    expect(studio.label).toBe('工作室模式');
    expect(studio.tagline).toContain('工厂流水线');
  });

  it('returns a fallback stub for unknown modes with the mode string as label', () => {
    const unknown = creationModeMeta('future-mode');
    expect(unknown.label).toBe('future-mode');
    expect(unknown.tagline).toBe('');
    expect(unknown.audience).toBe('');
  });

  it('handles nullish input without throwing', () => {
    // @ts-expect-error — exercise runtime fallback for nullish input
    const result = creationModeMeta(null);
    expect(result.label).toBe('未知模式');

    // @ts-expect-error — same for undefined
    const undefResult = creationModeMeta(undefined);
    expect(undefResult.label).toBe('未知模式');
  });
});

// ---------------------------------------------------------------------------
// resolveTodayPrimaryAction — Reading Power fallback case
// ---------------------------------------------------------------------------

describe('resolveTodayPrimaryAction', () => {
  it('returns Reading Power insight CTA when review-mode and no other signals', () => {
    // Review mode (isReviewer=true) + no pendingDecisions + no
    // pendingRipples + no batchActive + wizardProgressPct=100 → the
    // Reading Power fallback fires.
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      isReviewer: true,
      pendingDecisions: 0,
      pendingRipples: 0,
      batchActive: false,
      wizardProgressPct: 100,
      chaptersWritten: 5,
    });
    expect(action.id).toBe('insight');
    expect(action.label).toBe('查看追读力洞察');
    expect(action.nav).toBe('insight');
    expect(action.tab).toBe('overview');
    expect(action.reason).toContain('审阅模式');
  });

  it('prioritizes pending decisions over Reading Power fallback', () => {
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      isReviewer: true,
      pendingDecisions: 3,
      pendingRipples: 0,
      batchActive: false,
      wizardProgressPct: 100,
      chaptersWritten: 5,
    });
    expect(action.id).toBe('decisions');
    expect(action.label).toContain('3');
    expect(action.label).not.toContain('追读力');
  });

  it('prioritizes pending ripples over Reading Power fallback', () => {
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      isReviewer: true,
      pendingDecisions: 0,
      pendingRipples: 2,
      batchActive: false,
      wizardProgressPct: 100,
      chaptersWritten: 5,
    });
    expect(action.id).toBe('ripples');
    expect(action.label).toContain('2');
    expect(action.label).not.toContain('追读力');
  });

  it('does not return Reading Power fallback in non-review mode', () => {
    // Without isReviewer, the function picks decisions/ripples/
    // production CTAs — Reading Power fallback only fires in review mode
    // when all other priority signals are zero.
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      isReviewer: false,
      pendingDecisions: 0,
      pendingRipples: 0,
      batchActive: false,
      wizardProgressPct: 100,
      chaptersWritten: 5,
    });
    expect(action.id).not.toBe('insight');
    expect(action.label).not.toBe('查看追读力洞察');
  });
});
