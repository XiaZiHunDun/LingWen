/**
 * Phase 126 v16.5 #N.13 T4.P3.a — workbench-quality utility spec
 *
 * RED tests for the 3 utility functions behind `useWorkbenchQuality`:
 *   - summarizeLightValidation  (drops 2 casts at lines 204, 209)
 *   - runLightValidation       (drops 1 cast at line 234)
 *   - buildInlineConflictMarkers (drops 1 cast at line 284)
 *
 * The GREEN commit (T4.P3.b) will:
 *   - Tighten JSDoc on the 3 utility functions
 *   - Remove the 4 `as unknown as` casts from useWorkbenchQuality.ts
 *
 * Each test exercises the function bodies directly so any drift between
 * JSDoc and runtime behavior fails fast.
 */
import { describe, it, expect } from 'vitest';
import {
  summarizeLightValidation,
  runLightValidation,
} from '@/utils/creatorLightValidationUtils';
import { buildInlineConflictMarkers } from '@/utils/creatorInlineConflictUtils';

/**
 * Mirrors `LightValidationIssue` declared in
 * `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts`.
 *
 * Defined inline so the test does not depend on whether the composable re-exports
 * the interface. JSDoc on `runLightValidation` (T4.P3.b GREEN commit) must match
 * this shape so the `as unknown as LightValidationIssue[]` cast at line 234 can
 * be dropped without runtime drift.
 */
interface LightValidationIssue {
  id: string;
  kind?: string;
  level: 'warn' | 'info';
  label: string;
  paragraph?: number | null;
  rule?: string;
  fixHint?: string;
}

describe('summarizeLightValidation', () => {
  it('returns ok status for empty issues array', () => {
    const summary = summarizeLightValidation([]);
    expect(summary.status).toBe('ok');
    expect(summary.warnCount).toBe(0);
    expect(summary.infoCount).toBe(0);
  });

  it('returns warn status when any warn-level issue exists', () => {
    const issues: LightValidationIssue[] = [
      {
        id: 'light-long-1',
        kind: 'light',
        level: 'warn',
        label: '第 1 段偏长',
        paragraph: 1,
        rule: 'long_paragraph',
      },
      {
        id: 'light-stub',
        kind: 'light',
        level: 'info',
        label: '篇幅较短',
        paragraph: 1,
        rule: 'stub_chapter',
      },
    ];
    const summary = summarizeLightValidation(issues);
    expect(summary.status).toBe('warn');
    expect(summary.warnCount).toBe(1);
    expect(summary.infoCount).toBe(1);
  });

  it('returns info status when only info-level issues exist', () => {
    const issues: LightValidationIssue[] = [
      {
        id: 'light-empty',
        kind: 'light',
        level: 'info',
        label: '本章正文为空',
        paragraph: null,
        rule: 'empty_body',
      },
    ];
    const summary = summarizeLightValidation(issues);
    expect(summary.status).toBe('info');
    expect(summary.warnCount).toBe(0);
    expect(summary.infoCount).toBe(1);
  });
});

describe('runLightValidation', () => {
  it('returns empty array when chapter is null', () => {
    const issues = runLightValidation({ body: 'some body', chapter: null });
    expect(issues).toEqual([]);
  });

  it('returns empty array when chapter is undefined', () => {
    const issues = runLightValidation({ body: 'some body' });
    expect(issues).toEqual([]);
  });

  it('returns empty array for clean body content', () => {
    // Body must be >50 chars (stub_chapter guard) + balanced quotes + no duplicates
    const cleanBody =
      '干净的正文段落,这是一段较长的正文内容来确保超过五十个字符的最小长度限制,没有任何重复段落,没有触发任何规则。';
    const issues = runLightValidation({
      body: cleanBody,
      chapter: 1,
    });
    expect(issues).toEqual([]);
  });

  it('returns info issue for empty body', () => {
    const issues = runLightValidation({ body: '   ', chapter: 1 });
    expect(issues.length).toBeGreaterThan(0);
    expect(issues.some((i) => i.level === 'info' && i.rule === 'empty_body')).toBe(true);
  });
});

describe('buildInlineConflictMarkers', () => {
  it('returns empty array when chapter is null', () => {
    const markers = buildInlineConflictMarkers({
      chapter: null,
      deviations: [],
      logicIssues: [],
      lightIssues: [],
    });
    expect(markers).toEqual([]);
  });

  it('returns empty array when chapter is undefined', () => {
    const markers = buildInlineConflictMarkers({
      deviations: [],
      logicIssues: [],
      lightIssues: [],
    });
    expect(markers).toEqual([]);
  });

  it('returns empty array when there are no deviations/logic/light issues', () => {
    const markers = buildInlineConflictMarkers({
      chapter: 1,
      deviations: [],
      logicIssues: [],
      lightIssues: [],
    });
    expect(markers).toEqual([]);
  });

  it('builds deviation markers for matching chapter', () => {
    const markers = buildInlineConflictMarkers({
      chapter: 3,
      deviations: [
        { chapter: 3, severity: 'alert', message: '设定偏离示例', paragraph: 5 },
      ],
      logicIssues: [],
      lightIssues: [],
    });
    expect(markers.length).toBe(1);
    expect(markers[0].kind).toBe('deviation');
    expect(markers[0].label).toBe('设定偏离示例');
    expect(markers[0].paragraph).toBe(5);
  });

  it('skips deviations that target a different chapter', () => {
    const markers = buildInlineConflictMarkers({
      chapter: 3,
      deviations: [
        { chapter: 4, severity: 'warn', message: '其他章节的偏离', paragraph: 1 },
      ],
      logicIssues: [],
      lightIssues: [],
    });
    expect(markers).toEqual([]);
  });
});
