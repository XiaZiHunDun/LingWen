/**
 * API Client for 墨灵 Dashboard
 * Barrel re-export from domain-specific modules
 *
 * Phase 126 v16.2.8 T5: legacy creator.js + its 5 underlying modules (agent,
 * volumePlan, volumeTemplate, templateApproval, mergePreset) DELETED. All
 * re-exports below now point to typed wrappers (.ts). v16.2.6 memory +
 * v16.2.5 publish re-points are the canonical paths.
 *
 * Remaining .js files in this directory (NOT creator-domain, kept as-is):
 *   - core.js (request helper + error classes)
 *   - budgets.js (4 legacy budget funcs, used by dashboard not creator)
 *   - connectivity.js (ApiError offline tracking, used by core.js)
 *   - this file (barrel)
 */
export {
  fetchOverview,
  fetchChapters,
  fetchProductionRecords,
  fetchProductionRollup,
  fetchProductionCostTrend,
  fetchHealth,
} from './health.js';

export {
  fetchPendingDecisions,
  fetchAllDecisions,
  resolveDecision,
  deferDecision,
  cancelDecision,
} from './decisions.js';

export {
  fetchWorkflows,
  runWorkflow,
  resumeWorkflow,
  fetchActiveWorkflow,
  fetchWorkflowGraph,
} from './workflows.js';

export {
  fetchRipples,
  fetchRippleDetail,
  applyRipple,
  rejectRipple,
  fetchRippleStats,
  fetchReferenceGraph,
  fetchRippleAudit,
  rollbackRipple,
  fetchRippleCascade,
  fetchRipplePreview,
  fetchCascadeRuns,
  fetchAllCascadeRuns,
  cancelCascadeRun,
  fetchCascadeWithDepth,
} from './cvg.js';

export {
  fetchBudgets,
  fetchBudgetsByTier,
  setBudget,
  setBudgetByTier,
} from './budgets.js';

export {
  setStudioActive,
  fetchStudioSummary,
  fetchStudioQuality,
  fetchStudioQualityReport,
  fetchStudioProseDiff,
  fetchStudioProseJudge,
  studioProductionPreflight,
  studioProductionRun,
  fetchStudioActiveBatchJob,
  fetchStudioBatchJob,
} from './studio.js';

// Phase 126 v16.2.6 T5.b: memory aliases re-pointed from memory.js shim (deleted)
// to the api/memory.ts typed wrapper.
export {
  fetchCreatorMemoryAssets,
  saveCreatorMemoryAnnotation,
  queryCreatorMemory,
} from './memory.js';

// Phase 126 v16.2.5 T5.b: legacy aliases re-pointed from publish.js shim (deleted) to typed wrappers
export {
  fetchCreatorChapterPreview,
  saveCreatorChapterBody,
  saveCreatorChapterOutline,
} from './content.js';
export { generateCreatorVolumeSummary } from './volume.js';
export {
  exportCreatorEpub,
  exportCreatorDocx,
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
} from './export.js';

// Phase 126 v16.2.7 T5: creator_settings.ts DTO dedup keeps 6 LOCAL-ONLY classes
// (CreatorChapterPreviewResponse / CreatorChapterBodySaveRequest /
// CreatorChapterOutlineSaveRequest / CreatorTaskModelsPreferences /
// CreatorInterventionRules / CreatorModelOption). No barrel exports needed
// here — callers import directly from @/api/settings.