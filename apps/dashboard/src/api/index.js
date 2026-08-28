/**
 * API Client for 墨灵 Dashboard
 * Barrel re-export from domain-specific modules
 * (0 funcs, re-export only)
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
  fetchStudioProjects,
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

export {
  fetchCreatorOverview,
  runCreatorLogicCheck,
  runCreatorAgentPlan,
  runCreatorAgentPlanStream,
  fetchCreatorVolumePlan,
  saveCreatorVolumePlan,
  previewCreatorVolumePlanDiff,
  fetchCreatorBatchHistory,
  exportCreatorBatchHistory,
  mergeCreatorVolumePlan,
  splitCreatorVolumePlan,
  fetchCreatorVolumeTemplates,
  applyCreatorVolumeTemplate,
  saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate,
  renameCreatorVolumeTemplate,
  exportCreatorVolumeTemplates,
  importCreatorVolumeTemplates,
  fetchCreatorVolumeTemplateSyncSources,
  syncCreatorVolumeTemplates,
  publishCreatorVolumeTemplateToFactory,
  pullCreatorFactoryVolumeTemplates,
  deleteCreatorFactoryVolumeTemplate,
  fetchCreatorDiffCollabNotes,
  saveCreatorDiffCollabNotes,
  setCreatorVolumeTemplateVersion,
  fetchCreatorVolumeTemplateChangelog,
  rollbackCreatorVolumeTemplate,
  fetchCreatorTemplateApprovals,
  submitCreatorTemplateVersionApproval,
  approveCreatorTemplateApproval,
  rejectCreatorTemplateApproval,
  fetchCreatorTemplateApprovalChainConfig,
  saveCreatorTemplateApprovalChainConfig,
  fetchCreatorTemplateApprovalHistory,
  exportCreatorTemplateApprovalAudit,
  fetchCreatorTemplateApprovalSlaConfig,
  saveCreatorTemplateApprovalSlaConfig,
  fetchCreatorTemplateApprovalOverdue,
  transferCreatorTemplateApproval,
  fetchCreatorTemplateApprovalSnapshotDiff,
  fetchCreatorTemplateApprovalSnapshotDrift,
  batchApproveCreatorTemplateApprovals,
  batchRejectCreatorTemplateApprovals,
  preflightCreatorFactoryMergePresetPull,
  fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePresetPackages,
  exportCreatorMergePresetPackages,
  importCreatorMergePresetPackages,
  fetchCreatorFactoryMergePresetPackages,
  publishCreatorMergePresetToFactory,
  pullCreatorFactoryMergePresetPackages,
  applyCreatorMergePresetConflictFix,
  applyAllCreatorMergePresetConflictFixes,
  preflightCreatorMergePresetImport,
  previewCreatorMergePresetImportDiff,
  fetchCreatorMergePresetToposort,
  applyCreatorMergePresetToposort,
  dismissCreatorWizardPanel,
  saveCreatorWizardPanelCollapsed,
  fetchCreatorSettingsDocs,
  saveCreatorSettingsDocs,
  previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge,
  fetchCreatorMergePreferences,
  exportCreatorMergePreferences,
  importCreatorMergePreferences,
  fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot,
  fetchCreatorPreferences,
  fetchCreatorModels,
  saveCreatorPreferencesApi,
} from './creator.js';

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
