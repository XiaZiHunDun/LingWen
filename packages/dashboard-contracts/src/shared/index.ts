// Unified entry point for shared DTO types mirrored from lingwen-shared.
// Frontend consumers should import from '@lingwen/dashboard-contracts/shared'.

export * from './world';
export * from './workspace';
export * from './quality';
export * from './creator';
// Phase 126 v16.5 #N.10 — SSE event envelope types (now codegen-sourced;
// re-exports from lingwen-shared/src/lingwen_shared/contracts/ts/creator_sse)
export type {
  AdviceEvent,
  ChunkEvent,
  CreatorAgentPlanResult,
  CreatorAgentStreamEvent,
  DoneEvent,
  ErrorEvent,
  PreviewLabelEvent,
  StartEvent,
  StatusEvent,
} from './creator-sse';
export * from './settings';
export * from './onboarding';
// Phase 126 v16.5 #N.7 — re-exports from lingwen-shared TS codegen
export type {
  DatabaseStatusDTO,
  MemoryUsageDTO,
  HealthResponseDTO,
  OverviewResponseDTO,
  ChapterDataDTO,
  ChaptersResponseDTO,
  ProductionRecordResponseDTO,
  ProductionRecordsResponseDTO,
  ProductionBatchRollupResponseDTO,
  ProductionRollupResponseDTO,
  ProductionCostTrendPointResponseDTO,
  ProductionCostTrendResponseDTO,
} from './health';
export type {
  StudioProjectItemDTO,
  StudioProjectsResponseDTO,
  StudioActiveResponseDTO,
  StudioSetActiveRequestDTO,
  StudioSummaryResponseDTO,
  StudioQualityResponseDTO,
  StudioQualityReportIssueDTO,
  StudioQualityReportChapterDTO,
  StudioProseHeatmapChapterDTO,
  StudioProseHeatmapDTO,
  StudioQualityReportResponseDTO,
  StudioProseDiffTotalsDTO,
  StudioProseDiffChapterDTO,
  StudioProseDiffResponseDTO,
  StudioProseJudgeRatingDTO,
  StudioProseJudgeChapterDTO,
  StudioProseJudgeSignalDTO,
  StudioProseJudgeResponseDTO,
  StudioPreflightChapterDTO,
  StudioPreflightRequestDTO,
  StudioPreflightResponseDTO,
  StudioBatchRunRequestDTO,
  StudioBatchJobResponseDTO,
  StudioBatchJobSummaryDTO,
  StudioBatchJobListResponseDTO,
  StudioBatchTemplateDTO,
  StudioBatchTemplateCreateRequestDTO,
  StudioBatchTemplateListResponseDTO,
  StudioBatchTemplateUpdateRequestDTO,
} from './studio';
export type {
  WorkflowListItemDTO,
  RunWorkflowRequestDTO,
  ResumeWorkflowRequestDTO,
  WorkflowStatusResponseDTO,
  WorkflowMermaidResponseDTO,
} from './workflows';
export type {
  RippleListItemResponseDTO,
  RippleDetailResponseDTO,
  RippleActionResponseDTO,
  RippleStatsResponseDTO,
  RippleAuditEntryResponseDTO,
  CascadeNodeResponseDTO,
  CascadeEdgeResponseDTO,
  CascadeResponseDTO,
  CascadePreviewResponseDTO,
  ReferenceGraphResponseDTO,
  CascadeRunResponseDTO,
  CascadeCancelPayloadDTO,
} from './cvg';
export type {
  DecisionResponseDTO,
  ResolveDecisionRequestDTO,
  DeferDecisionRequestDTO,
  CancelDecisionRequestDTO,
} from './decisions';
