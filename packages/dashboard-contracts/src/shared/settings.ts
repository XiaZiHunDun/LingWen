// RE-EXPORTS from lingwen-shared (TS codegen output). Do not edit.
// Source: packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts
//
// Phase 126 v16.2.2 — Settings subdomain DTOs (added to creator.ts in T2).
// This shim splits them out for the typed wrapper (`apps/dashboard/src/api/settings.ts`)
// to import via `@lingwen/dashboard-contracts/shared` without dragging the entire
// creator.ts surface area into the import graph.

export type {
  CreatorFactoryMergePresetOperationResponse,
  CreatorMergePreferencesExportResponse,
  CreatorMergePreferencesImportRequest,
  CreatorMergePreferencesResponse,
  CreatorMergePresetChangelogEntry,
  CreatorMergePresetChangelogResponse,
  CreatorMergePresetConflict,
  CreatorMergePresetConflictFix,
  CreatorMergePresetConflictsResponse,
  CreatorMergePresetGraphEdge,
  CreatorMergePresetGraphNode,
  CreatorMergePresetGraphResponse,
  CreatorMergePresetImportPreviewResponse,
  CreatorMergePresetPackageDetail,
  CreatorMergePresetPackageSummary,
  CreatorMergePresetPublishRequest,
  CreatorMergePresetToposortResponse,
  CreatorSettingsDiffPart,
  CreatorSettingsDocsDiffResponse,
  CreatorSettingsDocsResponse,
  CreatorSettingsDocsSaveRequest,
  CreatorSettingsHistoryResponse,
  CreatorSettingsHistoryRestoreRequest,
  CreatorSettingsHistorySnapshot,
  CreatorSettingsMergeFieldPreview,
  CreatorSettingsMergeStrategyResponse,
  CreatorSettingsThreeWayDiffResponse,
  CreatorSettingsThreeWayPair,
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/creator';
