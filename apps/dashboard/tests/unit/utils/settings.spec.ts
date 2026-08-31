/**
 * Phase 126 v16.5 #N.13 T4.P3.e — settings utility spec (RED tests)
 *
 * Locks the JSDoc-typed surface of 4 utility functions behind the LAST 8
 * `as unknown as` casts in `apps/dashboard/src/composables/useCreatorSettings/`:
 *
 *   settingsDocsUtils.js
 *     - parseSettingsDocs  (drops 5 casts at lines 79, 82, 83, 85, 86 of useSettingsDocs.ts)
 *
 *   settingsHistoryUtils.js
 *     - parseSettingsHistory  (drops 1 cast at line 65 of useSettingsHistory.ts)
 *
 *   mergePresetsUtils.js
 *     - parseMergePreferences       (drops 1 cast at line 129 of useMergePresets.ts)
 *     - parseMergePresetImportPreview  (drops 1 cast at line 245 of useMergePresets.ts)
 *
 * RED: utility files do not exist yet — tests fail at import resolution.
 *      Tests assert the runtime data shape so the JSDoc contract (T4.P3.f GREEN)
 *      must match what the composables actually consume.
 *
 * Why preserve legacy fallbacks:
 *   - use-settings-docs.spec.ts at line 78-88 exercises `pillars` / `outline`
 *     legacy alias handling (typed wrapper returns snake_case only, but the
 *     composable must accept pre-v16.2.2 camelCase responses for backward
 *     compat).
 *   - use-settings-history.spec.ts at line 53-61 exercises the `history` key
 *     fallback. Per T4.P3 spec: "Verify no test depends on the `history` field
 *     before removing." A test DOES depend on it — keep the fallback.
 */
import { describe, it, expect } from 'vitest';
import { parseSettingsDocs } from '@/utils/settingsDocsUtils';
import { parseSettingsHistory } from '@/utils/settingsHistoryUtils';
import {
  parseMergePreferences,
  parseMergePresetImportPreview,
} from '@/utils/mergePresetsUtils';

describe('parseSettingsDocs', () => {
  it('returns canonical snake_case pillars_text + global_outline_text', () => {
    const result = parseSettingsDocs({
      pillars_text: '支柱 A',
      global_outline_text: '大纲 B',
    });
    expect(result.pillars).toBe('支柱 A');
    expect(result.outline).toBe('大纲 B');
  });

  it('falls back to legacy camelCase pillars/outline keys', () => {
    // Pre-v16.2.2 backend responses used camelCase. Preserved for backward compat.
    const result = parseSettingsDocs({
      pillars: 'legacy pillars',
      outline: 'legacy outline',
    });
    expect(result.pillars).toBe('legacy pillars');
    expect(result.outline).toBe('legacy outline');
  });

  it('prefers snake_case when both key sets are present', () => {
    const result = parseSettingsDocs({
      pillars_text: 'new pillars',
      global_outline_text: 'new outline',
      pillars: 'old pillars',
      outline: 'old outline',
    });
    expect(result.pillars).toBe('new pillars');
    expect(result.outline).toBe('new outline');
  });

  it('returns empty strings for missing fields', () => {
    const result = parseSettingsDocs({});
    expect(result.pillars).toBe('');
    expect(result.outline).toBe('');
  });

  it('coerces non-string values to string via String()', () => {
    // The canonical DTO types these as `string`, but pre-v16.2.2 responses
    // could send numeric or null. The utility must coerce via String() so
    // callers can assign to `Ref<string>`. Cast to a loose shape to simulate
    // a malformed legacy response.
    const result = parseSettingsDocs(
      { pillars_text: 123, global_outline_text: null } as unknown as Record<string, unknown>,
    );
    expect(result.pillars).toBe('123');
    expect(result.outline).toBe('');
  });

  it('tolerates null/undefined input', () => {
    expect(parseSettingsDocs(null).pillars).toBe('');
    expect(parseSettingsDocs(undefined).outline).toBe('');
  });
});

describe('parseSettingsHistory', () => {
  it('returns snapshots array from canonical CreatorSettingsHistoryResponse', () => {
    const result = parseSettingsHistory({
      slug: 'demo',
      count: 2,
      snapshots: [
        { id: 'snap-1', saved_at: '2026-06-01T00:00:00Z', label: 'a' },
        { id: 'snap-2', saved_at: '2026-06-02T00:00:00Z', label: 'b' },
      ],
    });
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('snap-1');
    expect(result[1].id).toBe('snap-2');
  });

  it('falls back to legacy `history` key for pre-v16.2.2 backend responses', () => {
    const result = parseSettingsHistory({
      history: [{ id: 'legacy-1', saved_at: '2026-05-01T00:00:00Z' }],
    });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('legacy-1');
  });

  it('prefers snapshots over history when both keys present', () => {
    const result = parseSettingsHistory({
      snapshots: [{ id: 'canonical-1' }],
      history: [{ id: 'legacy-1' }],
    });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('canonical-1');
  });

  it('returns empty array when both keys missing', () => {
    expect(parseSettingsHistory({})).toEqual([]);
    expect(parseSettingsHistory(null)).toEqual([]);
    expect(parseSettingsHistory(undefined)).toEqual([]);
  });
});

describe('parseMergePreferences', () => {
  it('preserves pillars_merge_source + global_outline_merge_source', () => {
    const result = parseMergePreferences({
      pillars_merge_source: 'history',
      global_outline_merge_source: 'editor',
    });
    expect(result.pillars_merge_source).toBe('history');
    expect(result.global_outline_merge_source).toBe('editor');
  });

  it('returns plain record for the legacy loose-shape callers', () => {
    // use-merge-presets.spec.ts:101 mocks with { style: 'auto' } and reads
    // .style back. The utility must return a plain dict so caller-side test
    // mocks work without typing coercion.
    const result = parseMergePreferences({ style: 'auto' });
    expect(result.style).toBe('auto');
  });

  it('returns empty record for missing/null/undefined input', () => {
    expect(parseMergePreferences({})).toEqual({});
    expect(parseMergePreferences(null)).toEqual({});
    expect(parseMergePreferences(undefined)).toEqual({});
  });
});

describe('parseMergePresetImportPreview', () => {
  it('returns added/updated/removed from canonical preview response', () => {
    const result = parseMergePresetImportPreview({
      added: ['pkg-a'],
      updated: [{ id: 'pkg-b' }],
      removed: ['pkg-c'],
      unchanged_count: 5,
    });
    expect(result.added).toEqual(['pkg-a']);
    expect(result.updated).toEqual([{ id: 'pkg-b' }]);
    expect(result.removed).toEqual(['pkg-c']);
  });

  it('returns empty arrays when preview fields missing', () => {
    const result = parseMergePresetImportPreview({});
    expect(result.added).toEqual([]);
    expect(result.updated).toEqual([]);
    expect(result.removed).toEqual([]);
  });

  it('tolerates null/undefined input', () => {
    expect(parseMergePresetImportPreview(null).added).toEqual([]);
    expect(parseMergePresetImportPreview(undefined).removed).toEqual([]);
  });
});
