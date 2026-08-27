/**
 * Settings API client — typed wrapper around /creator/settings-docs* endpoints.
 *
 * Types come from @lingwen/dashboard-contracts/shared/settings (which mirrors
 * packages/lingwen-shared Pydantic DTOs via codegen).
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.2 (Phase 126 T3).
 * Existing api/mergePreset.js continues to handle backward-compatible calls.
 * Future v16.2+ phases will switch them over.
 *
 * v16.2.1 lessons enforced:
 * - NO `/api/` prefix in URL paths (BASE_URL is `/api`)
 * - NO zod runtime validation (zod is T5 CI drift, not wrapper layer)
 * - NO request alias for factory_op / factory_pull / factory_resolve — they share
 *   the same response shape (`CreatorFactoryMergePresetOperationResponse`)
 * - Per T2 reviewer: `publishMergePresetToFactory()`,
 *   `pullFactoryMergePresetsToProject()`, `resolveFactoryMergePresetConflict()`,
 *   and `deleteFactoryMergePresetPackage()` all collapse to the generic factory
 *   operation response.
 *
 * Local `XxxLocal*` types below exist ONLY for endpoints whose request/response
 * DTOs are not yet in `@lingwen/dashboard-contracts/shared/settings` (28 DTOs
 * migrated in T2; ~20+ still pending migration to lingwen-shared in v16.2.x).
 * They mirror the Python source in `apps/studio_api/models/creator_merge.py`
 * and will be replaced by imported types once those DTOs land in shared.
 */
import type {
  CreatorFactoryMergePresetOperationResponse,
  CreatorMergePreferencesExportResponse,
  CreatorMergePreferencesImportRequest,
  CreatorMergePreferencesResponse,
  CreatorMergePresetChangelogResponse,
  CreatorMergePresetConflictsResponse,
  CreatorMergePresetConflictFix,
  CreatorMergePresetGraphResponse,
  CreatorMergePresetImportPreviewResponse,
  CreatorMergePresetPackageSummary,
  CreatorMergePresetPublishRequest,
  CreatorMergePresetToposortResponse,
  CreatorSettingsDocsDiffResponse,
  CreatorSettingsDocsResponse,
  CreatorSettingsDocsSaveRequest,
  CreatorSettingsHistoryResponse,
  CreatorSettingsHistoryRestoreRequest,
  CreatorSettingsMergeStrategyResponse,
  CreatorSettingsThreeWayDiffResponse,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// Local DTOs — pending migration to @lingwen/dashboard-contracts/shared/settings
// (mirrored from apps/studio_api/models/creator_merge.py — see file header)
// ---------------------------------------------------------------------------

interface CreatorSettingsMergePreviewRequest {
  pillars_text: string;
  global_outline_text: string;
  pillars_merge_source?: string;
  global_outline_merge_source?: string;
  snapshot_id?: string | null;
  pillars_merge_snapshot_id?: string | null;
  global_outline_merge_snapshot_id?: string | null;
}

interface CreatorSettingsThreeWayRequest {
  pillars_text: string;
  global_outline_text: string;
  snapshot_id?: string | null;
}

interface CreatorMergePreferencesImportResponse {
  scope: string;
  project?: Record<string, unknown> | null;
  global_prefs?: Record<string, unknown> | null;
}

interface CreatorMergePresetPackagesResponse {
  packages: CreatorMergePresetPackageSummary[];
}

interface CreatorMergePresetConflictFixesResponse {
  fix_count: number;
  fixes: CreatorMergePresetConflictFix[];
}

interface CreatorMergePresetConflictFixApplyRequest {
  package_id: string;
  action: string;
  dependency_id?: string | null;
  version_label?: string | null;
}

interface CreatorMergePresetConflictFixApplyResponse {
  package_id: string;
  action: string;
  conflict_count: number;
  package: CreatorMergePresetPackageSummary;
}

interface CreatorMergePresetApplyAllFixesResponse {
  applied: number;
  conflict_count: number;
}

interface CreatorMergePresetToposortApplyResponse {
  reordered: number;
  order: string[];
}

interface CreatorMergePresetFactoryConflictResponse {
  conflict_count: number;
  conflicts: Array<{
    type: string;
    package_id: string;
    dependency_id?: string | null;
    path?: string[];
    message?: string;
  }>;
}

interface CreatorMergePresetFactoryConflictResolveRequest {
  package_id: string;
  strategy?: string;
}

interface CreatorMergePresetFactoryPullPreflightResponse {
  would_import: number;
  conflict_count: number;
  conflicts: Array<{
    type: string;
    package_id: string;
    dependency_id?: string | null;
    path?: string[];
    message?: string;
  }>;
  blocked: boolean;
}

interface CreatorMergePresetFactoryPullRequest {
  package_ids: string[];
  conflict_strategies?: Record<string, string>;
}

interface CreatorMergePresetFactoryDeleteResponse {
  id: string;
  deleted: boolean;
}

interface CreatorMergePresetChangelogDiffResponse {
  package_id: string;
  entry_index: number;
  changed_at?: string | null;
  action?: string | null;
  change_count: number;
  changes: Array<{
    field: string;
    before: unknown;
    after: unknown;
  }>;
}

interface CreatorMergePresetPackagesExportResponse {
  schema_version: string;
  packages: Record<string, unknown>[];
  count: number;
}

interface CreatorMergePresetPackagesImportRequest {
  schema_version?: string | null;
  packages: Record<string, unknown>[];
  replace?: boolean;
}

interface CreatorMergePresetPackagesImportResponse {
  imported: number;
  total: number;
  replaced: boolean;
  packages: CreatorMergePresetPackageSummary[];
}

// ---------------------------------------------------------------------------
// /creator/settings-docs (GET, PUT, preview, three-way-preview, merge-preview)
// ---------------------------------------------------------------------------

export async function fetchSettingsDocs(): Promise<CreatorSettingsDocsResponse> {
  const data = await request('/creator/settings-docs');
  return data as CreatorSettingsDocsResponse;
}

export async function saveSettingsDocs(
  req: CreatorSettingsDocsSaveRequest,
): Promise<CreatorSettingsDocsResponse> {
  const data = await request('/creator/settings-docs', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorSettingsDocsResponse;
}

export async function previewSettingsDocsDiff(
  req: CreatorSettingsDocsSaveRequest,
): Promise<CreatorSettingsDocsDiffResponse> {
  const data = await request('/creator/settings-docs/preview', {
    method: 'POST',
    body: req,
  });
  return data as CreatorSettingsDocsDiffResponse;
}

export async function previewSettingsThreeWay(
  req: CreatorSettingsThreeWayRequest,
): Promise<CreatorSettingsThreeWayDiffResponse> {
  const data = await request('/creator/settings-docs/three-way-preview', {
    method: 'POST',
    body: req,
  });
  return data as CreatorSettingsThreeWayDiffResponse;
}

export async function previewSettingsMergeStrategy(
  req: CreatorSettingsMergePreviewRequest,
): Promise<CreatorSettingsMergeStrategyResponse> {
  const data = await request('/creator/settings-docs/merge-preview', {
    method: 'POST',
    body: req,
  });
  return data as CreatorSettingsMergeStrategyResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/history (GET)
// /creator/settings-docs/restore (POST)
// ---------------------------------------------------------------------------

export async function fetchSettingsHistory(): Promise<CreatorSettingsHistoryResponse> {
  const data = await request('/creator/settings-docs/history');
  return data as CreatorSettingsHistoryResponse;
}

export async function restoreSettingsSnapshot(
  req: CreatorSettingsHistoryRestoreRequest,
): Promise<CreatorSettingsDocsResponse> {
  const data = await request('/creator/settings-docs/restore', {
    method: 'POST',
    body: req,
  });
  return data as CreatorSettingsDocsResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences
// (GET, /global GET, /export GET, /import POST)
// ---------------------------------------------------------------------------

export async function fetchMergePreferences(): Promise<CreatorMergePreferencesResponse> {
  const data = await request('/creator/settings-docs/merge-preferences');
  return data as CreatorMergePreferencesResponse;
}

export async function fetchGlobalMergePreferences(): Promise<CreatorMergePreferencesResponse> {
  const data = await request('/creator/settings-docs/merge-preferences/global');
  return data as CreatorMergePreferencesResponse;
}

export async function exportMergePreferences(): Promise<CreatorMergePreferencesExportResponse> {
  const data = await request('/creator/settings-docs/merge-preferences/export');
  return data as CreatorMergePreferencesExportResponse;
}

export async function importMergePreferences(
  req: CreatorMergePreferencesImportRequest,
): Promise<CreatorMergePreferencesImportResponse> {
  const data = await request('/creator/settings-docs/merge-preferences/import', {
    method: 'POST',
    body: req,
  });
  return data as CreatorMergePreferencesImportResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences/preset-packages (list + factory list)
// ---------------------------------------------------------------------------

export async function listMergePresetPackages(): Promise<CreatorMergePresetPackagesResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages',
  );
  return data as CreatorMergePresetPackagesResponse;
}

export async function listFactoryMergePresetPackages(): Promise<CreatorMergePresetPackagesResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/factory',
  );
  return data as CreatorMergePresetPackagesResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences/preset-packages/graph
// ---------------------------------------------------------------------------

export async function buildMergePresetGraph(): Promise<CreatorMergePresetGraphResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/graph',
  );
  return data as CreatorMergePresetGraphResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences/preset-packages/conflicts (project)
// + /conflicts/fixes (suggest) + apply-fix + apply-all
// ---------------------------------------------------------------------------

export async function detectMergePresetConflicts(): Promise<CreatorMergePresetConflictsResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/conflicts',
  );
  return data as CreatorMergePresetConflictsResponse;
}

export async function suggestMergePresetFixes(): Promise<CreatorMergePresetConflictFixesResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/conflicts/fixes',
  );
  return data as CreatorMergePresetConflictFixesResponse;
}

export async function applyMergePresetConflictFix(
  req: CreatorMergePresetConflictFixApplyRequest,
): Promise<CreatorMergePresetConflictFixApplyResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-fix',
    { method: 'POST', body: req },
  );
  return data as CreatorMergePresetConflictFixApplyResponse;
}

export async function applyAllMergePresetConflictFixes(): Promise<CreatorMergePresetApplyAllFixesResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-all',
    { method: 'POST' },
  );
  return data as CreatorMergePresetApplyAllFixesResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences/preset-packages/toposort
// + /toposort/apply
// ---------------------------------------------------------------------------

export async function toposortMergePresetPackages(): Promise<CreatorMergePresetToposortResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/toposort',
  );
  return data as CreatorMergePresetToposortResponse;
}

export async function applyToposortMergePresetOrder(): Promise<CreatorMergePresetToposortApplyResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/toposort/apply',
    { method: 'POST' },
  );
  return data as CreatorMergePresetToposortApplyResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences/preset-packages/import/*
// preview-diff + preflight + export + import
// ---------------------------------------------------------------------------

export async function previewMergePresetImportDiff(
  req: CreatorMergePresetPackagesImportRequest,
): Promise<CreatorMergePresetImportPreviewResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/import/preview-diff',
    { method: 'POST', body: req },
  );
  return data as CreatorMergePresetImportPreviewResponse;
}

export async function preflightMergePresetImport(
  req: CreatorMergePresetPackagesImportRequest,
): Promise<CreatorMergePresetFactoryPullPreflightResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/import/preflight',
    { method: 'POST', body: req },
  );
  return data as CreatorMergePresetFactoryPullPreflightResponse;
}

export async function exportMergePresetPackages(): Promise<CreatorMergePresetPackagesExportResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/export',
  );
  return data as CreatorMergePresetPackagesExportResponse;
}

export async function importMergePresetPackages(
  req: CreatorMergePresetPackagesImportRequest,
): Promise<CreatorMergePresetPackagesImportResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/import',
    { method: 'POST', body: req },
  );
  return data as CreatorMergePresetPackagesImportResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences/preset-packages/factory/*
// conflicts + merge-conflicts + publish + pull-preflight + pull + delete
// ---------------------------------------------------------------------------

export async function detectFactoryMergePresetConflicts(): Promise<CreatorMergePresetFactoryConflictResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/factory/conflicts',
  );
  return data as CreatorMergePresetFactoryConflictResponse;
}

export async function resolveFactoryMergePresetConflict(
  req: CreatorMergePresetFactoryConflictResolveRequest,
): Promise<CreatorFactoryMergePresetOperationResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/factory/merge-conflicts',
    { method: 'POST', body: req },
  );
  return data as CreatorFactoryMergePresetOperationResponse;
}

export async function publishMergePresetToFactory(
  req: CreatorMergePresetPublishRequest,
): Promise<CreatorFactoryMergePresetOperationResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/factory/publish',
    { method: 'POST', body: req },
  );
  return data as CreatorFactoryMergePresetOperationResponse;
}

export async function preflightFactoryMergePresetPull(
  req: CreatorMergePresetFactoryPullRequest,
): Promise<CreatorMergePresetFactoryPullPreflightResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/factory/pull/preflight',
    { method: 'POST', body: req },
  );
  return data as CreatorMergePresetFactoryPullPreflightResponse;
}

export async function pullFactoryMergePresetsToProject(
  req: CreatorMergePresetFactoryPullRequest,
): Promise<CreatorFactoryMergePresetOperationResponse> {
  const data = await request(
    '/creator/settings-docs/merge-preferences/preset-packages/factory/pull',
    { method: 'POST', body: req },
  );
  return data as CreatorFactoryMergePresetOperationResponse;
}

export async function deleteFactoryMergePresetPackage(
  packageId: string,
): Promise<CreatorMergePresetFactoryDeleteResponse> {
  const data = await request(
    `/creator/settings-docs/merge-preferences/preset-packages/factory/${encodeURIComponent(packageId)}`,
    { method: 'DELETE' },
  );
  return data as CreatorMergePresetFactoryDeleteResponse;
}

// ---------------------------------------------------------------------------
// /creator/settings-docs/merge-preferences/preset-packages/{package_id}/changelog
// + /changelog/diff
// ---------------------------------------------------------------------------

export async function fetchMergePresetChangelog(
  packageId: string,
  limit = 10,
): Promise<CreatorMergePresetChangelogResponse> {
  const data = await request(
    `/creator/settings-docs/merge-preferences/preset-packages/${encodeURIComponent(packageId)}/changelog?limit=${encodeURIComponent(String(limit))}`,
  );
  return data as CreatorMergePresetChangelogResponse;
}

export async function fetchMergePresetChangelogDiff(
  packageId: string,
  entryIndex = 0,
): Promise<CreatorMergePresetChangelogDiffResponse> {
  const data = await request(
    `/creator/settings-docs/merge-preferences/preset-packages/${encodeURIComponent(packageId)}/changelog/diff?entry_index=${encodeURIComponent(String(entryIndex))}`,
  );
  return data as CreatorMergePresetChangelogDiffResponse;
}
