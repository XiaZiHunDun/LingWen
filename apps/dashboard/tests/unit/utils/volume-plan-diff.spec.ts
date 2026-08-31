/**
 * Phase 126 v16.5 #N.13 T4.P3.c — volume-plan-diff utility JSDoc contract tests
 *
 * Locks the JSDoc-typed surface of `volumePlanDiffExportUtils.js` so the
 * composables in `useCreatorVolumePlanDiff/` + `useCreatorVolumePlanTemplates/`
 * can drop the `as unknown as` casts at the typed-wrapper boundary.
 *
 * RED: import resolves, JSDoc-typed signature is too loose (object/object[]).
 *      Calls succeed at runtime but the runtime data shape is undocumented.
 * GREEN: tighten JSDoc on `buildVolumePlanDiffMarkdown` +
 *        `buildVolumePlanDiffExportPayload` + add `typedEditableVolumesForDiff`
 *        helper that produces `CreatorVolumePlanEntry[]`.
 */
import { describe, it, expect } from 'vitest';
import type { CreatorVolumePlanEntry } from '@lingwen/dashboard-contracts/shared';
import {
  buildVolumePlanDiffMarkdown,
  buildVolumePlanDiffExportPayload,
  typedEditableVolumesForDiff,
} from '@/composables/volumePlanDiffExportUtils';

const baseChanges = [
  { type: 'add', label: 'vol1', message: '新增卷一', details: ['detail-a'] },
  { type: 'modify', label: 'vol2', message: '调整卷二核心冲突' },
];

const basePreview = {
  has_changes: true,
  changes: baseChanges,
  global_outline_path: '/outline.md',
  global_outline_excerpt: 'excerpt',
  global_outline_lines: [],
};

const baseUiProfile = {
  volume_plan_diff_export_outline: true,
  volume_plan_diff_export_highlight: false,
};

describe('volumePlanDiffExportUtils — typed input contract', () => {
  it('buildVolumePlanDiffMarkdown accepts strict-shape changes and returns markdown', () => {
    const md = buildVolumePlanDiffMarkdown(
      baseChanges,
      basePreview,
      baseUiProfile,
    );
    expect(md).toContain('变更数：2');
    expect(md).toContain('add');
    expect(md).toContain('vol1');
    expect(md).toContain('detail-a');
    expect(md).toContain('excerpt');
  });

  it('buildVolumePlanDiffExportPayload accepts strict-shape changes and returns payload', () => {
    const payload = buildVolumePlanDiffExportPayload(
      baseChanges,
      basePreview,
      baseUiProfile,
    );
    expect(payload.schema_version).toBe('1');
    expect(payload.has_changes).toBe(true);
    expect(payload.change_count).toBe(2);
    expect(payload.changes).toEqual(baseChanges);
    expect(payload.global_outline_path).toBe('/outline.md');
    expect(payload.global_outline_excerpt).toBe('excerpt');
  });

  it('typedEditableVolumesForDiff narrows loose volumes to CreatorVolumePlanEntry[]', () => {
    // Loose source shape (same as editableVolumes ref in useCreatorVolumePlan).
    const loose: Array<Record<string, unknown>> = [
      {
        label: 'vol1',
        start_chapter: 1,
        end_chapter: 10,
        core_conflict: 'none',
        locked: false,
      },
    ];
    const narrowed = typedEditableVolumesForDiff(loose);
    // Per-item spread preserves the surface; assignment to CreatorVolumePlanEntry[]
    // is gated by the JSDoc `@returns` annotation in volumePlanDiffExportUtils.js.
    const typed: CreatorVolumePlanEntry[] = narrowed;
    expect(typed).toHaveLength(1);
    expect(typed[0].label).toBe('vol1');
    expect(typed[0].start_chapter).toBe(1);
    expect(typed[0].end_chapter).toBe(10);
  });

  it('typedEditableVolumesForDiff preserves order and omits extras', () => {
    const loose: Array<Record<string, unknown>> = [
      { label: 'a', start_chapter: 1, end_chapter: 5 },
      { label: 'b', start_chapter: 6, end_chapter: 10, locked: true },
      { label: 'c', start_chapter: 11, end_chapter: 20, core_conflict: 'resolves' },
    ];
    const typed = typedEditableVolumesForDiff(loose);
    expect(typed.map((v) => v.label)).toEqual(['a', 'b', 'c']);
    expect(typed[1].locked).toBe(true);
    expect(typed[2].core_conflict).toBe('resolves');
  });
});
