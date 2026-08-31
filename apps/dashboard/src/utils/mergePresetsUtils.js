/**
 * mergePresetsUtils — typed boundary for `useMergePresets` data normalization
 *
 * Phase 126 v16.5 #N.13 T4.P3.f — drops 2 `as unknown as` casts at lines
 * 129 and 245 of `composables/useCreatorSettings/useMergePresets.ts`.
 *
 * The composable previously inlined `data as unknown as MergePreferences` and
 * `data as unknown as { added, updated, removed }`. Now both transformations
 * live here with JSDoc-typed inputs/outputs so call sites drop their casts.
 *
 * `parseMergePreferences` returns a **plain dict** (not the strict
 * `CreatorMergePreferencesResponse`) because the existing ref type
 * `MergePreferences = { [key: string]: unknown }` is intentionally loose —
 * `use-merge-presets.spec.ts:101` mocks with `{ style: 'auto' }` and reads
 * `.style` back, so the utility must allow arbitrary extra fields.
 *
 * @typedef {import('@lingwen/dashboard-contracts/shared').CreatorMergePreferencesResponse} CreatorMergePreferencesResponse
 * @typedef {import('@lingwen/dashboard-contracts/shared').CreatorMergePresetImportPreviewResponse} CreatorMergePresetImportPreviewResponse
 */

/**
 * Normalize a merge-preferences response to a plain dict.
 *
 * `MergePreferences` ref shape is `{ [key: string]: unknown }` so the
 * canonical `CreatorMergePreferencesResponse` is widened to a plain record
 * here. The original fields (`pillars_merge_source`,
 * `global_outline_merge_source`, etc.) are preserved as-is.
 *
 * @param {CreatorMergePreferencesResponse | Record<string, unknown> | null | undefined} data
 * @returns {Record<string, unknown>}
 */
export function parseMergePreferences(data) {
  if (!data || typeof data !== 'object') return {};
  return { ...data };
}

/**
 * Normalize a merge-preset import-preview response to
 * `{ added, updated, removed }` arrays. Missing fields become empty arrays.
 *
 * @param {CreatorMergePresetImportPreviewResponse | null | undefined} data
 * @returns {{ added: unknown[], updated: unknown[], removed: unknown[] }}
 */
export function parseMergePresetImportPreview(data) {
  return {
    added: Array.isArray(data?.added) ? data.added : [],
    updated: Array.isArray(data?.updated) ? data.updated : [],
    removed: Array.isArray(data?.removed) ? data.removed : [],
  };
}
