// tests/unit/volume-plan-diff-export-utils.spec.ts — 卷纲 diff 导出工具纯函数

import { describe, test, expect } from 'vitest';
import {
  buildVolumePlanDiffExportPayload,
  buildVolumePlanDiffMarkdown,
  decodeVolumePlanDiffShareToken,
  detectShareVolumeMergeConflicts,
  encodeVolumePlanDiffShareToken,
  parseVolumePlanDiffShareHash,
} from '../../src/composables/volumePlanDiffExportUtils.js';

describe('volumePlanDiffExportUtils', () => {
  const preview = {
    has_changes: true,
    global_outline_path: 'docs/outline.md',
    global_outline_excerpt: '第一卷开篇',
    global_outline_lines: [{ text: '第一卷', highlighted: true }],
  };
  const uiProfile = {
    volume_plan_diff_export_outline: true,
    volume_plan_diff_export_highlight: true,
  };
  const changes = [
    { type: 'modified', label: '第一卷', message: '章节范围变更', details: ['1-10 → 1-12'] },
  ];

  test('buildVolumePlanDiffMarkdown includes outline excerpt when enabled', () => {
    const md = buildVolumePlanDiffMarkdown(changes, preview, uiProfile);
    expect(md).toContain('第一卷开篇');
    expect(md).toContain('modified');
    expect(md).toContain('高亮行');
  });

  test('buildVolumePlanDiffExportPayload carries highlight metadata', () => {
    const payload = buildVolumePlanDiffExportPayload(changes, preview, uiProfile);
    expect(payload.change_count).toBe(1);
    expect(payload.highlighted_changes).toHaveLength(1);
    expect(payload.highlighted_outline_lines).toHaveLength(1);
  });

  test('share token round-trip preserves draft volumes', () => {
    const payload = buildVolumePlanDiffExportPayload(changes, preview, uiProfile);
    const draft = [{ label: '第一卷', start_chapter: 1, end_chapter: 12, core_conflict: 'x', locked: false }];
    const token = encodeVolumePlanDiffShareToken(payload, draft, { 第一卷: 'note' });
    const parsed = decodeVolumePlanDiffShareToken(token);
    expect(parsed.valid).toBe(true);
    expect(parsed.draft_volumes).toHaveLength(1);
    expect(parsed.collab_notes).toEqual({ 第一卷: 'note' });
    expect(parsed.can_apply).toBe(true);
  });

  test('parseVolumePlanDiffShareHash reads creator-diff fragment', () => {
    const payload = buildVolumePlanDiffExportPayload(changes, preview, uiProfile);
    const token = encodeVolumePlanDiffShareToken(payload);
    const parsed = parseVolumePlanDiffShareHash(`#creator-diff=${token}`);
    expect(parsed?.change_count).toBe(1);
  });

  test('detectShareVolumeMergeConflicts flags label conflicts', () => {
    const parsed = {
      draft_volumes: [{ label: '第一卷', start_chapter: 1, end_chapter: 20, core_conflict: 'new', locked: false }],
    };
    const local = [{ label: '第一卷', start_chapter: 1, end_chapter: 10, core_conflict: 'old', locked: false }];
    const conflicts = detectShareVolumeMergeConflicts(parsed, local);
    expect(conflicts).toHaveLength(1);
    expect(conflicts[0].label).toBe('第一卷');
  });
});
