// Phase 126 v16.5 #N.7: re-export Studio DTOs from lingwen-shared TS codegen.
import type {
  StudioProjectItem,
  StudioProjectsResponse,
  StudioActiveResponse,
  StudioSetActiveRequest,
  StudioSummaryResponse,
  StudioQualityResponse,
  StudioQualityReportIssue,
  StudioQualityReportChapter,
  StudioProseHeatmapChapter,
  StudioProseHeatmap,
  StudioQualityReportResponse,
  StudioProseDiffTotals,
  StudioProseDiffChapter,
  StudioProseDiffResponse,
  StudioProseJudgeRating,
  StudioProseJudgeChapter,
  StudioProseJudgeSignal,
  StudioProseJudgeResponse,
  StudioPreflightChapter,
  StudioPreflightRequest,
  StudioPreflightResponse,
  StudioBatchRunRequest,
  StudioBatchJobResponse,
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/studio';

export type StudioProjectItemDTO = StudioProjectItem;
export type StudioProjectsResponseDTO = StudioProjectsResponse;
export type StudioActiveResponseDTO = StudioActiveResponse;
export type StudioSetActiveRequestDTO = StudioSetActiveRequest;
export type StudioSummaryResponseDTO = StudioSummaryResponse;
export type StudioQualityResponseDTO = StudioQualityResponse;
export type StudioQualityReportIssueDTO = StudioQualityReportIssue;
export type StudioQualityReportChapterDTO = StudioQualityReportChapter;
export type StudioProseHeatmapChapterDTO = StudioProseHeatmapChapter;
export type StudioProseHeatmapDTO = StudioProseHeatmap;
export type StudioQualityReportResponseDTO = StudioQualityReportResponse;
export type StudioProseDiffTotalsDTO = StudioProseDiffTotals;
export type StudioProseDiffChapterDTO = StudioProseDiffChapter;
export type StudioProseDiffResponseDTO = StudioProseDiffResponse;
export type StudioProseJudgeRatingDTO = StudioProseJudgeRating;
export type StudioProseJudgeChapterDTO = StudioProseJudgeChapter;
export type StudioProseJudgeSignalDTO = StudioProseJudgeSignal;
export type StudioProseJudgeResponseDTO = StudioProseJudgeResponse;
export type StudioPreflightChapterDTO = StudioPreflightChapter;
export type StudioPreflightRequestDTO = StudioPreflightRequest;
export type StudioPreflightResponseDTO = StudioPreflightResponse;
export type StudioBatchRunRequestDTO = StudioBatchRunRequest;
export type StudioBatchJobResponseDTO = StudioBatchJobResponse;
