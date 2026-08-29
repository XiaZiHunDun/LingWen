// Phase 126 v16.5 #7: Studio DTOs (manually declared, not codegen).
//
// Wraps endpoints:
//   GET /studio/projects, /studio/active, /studio/summary, /studio/quality,
//       /studio/quality-report, /studio/prose-diff, /studio/prose-judge,
//   PUT /studio/active
//   POST /studio/production/preflight, /studio/production/run
//   GET /studio/production/jobs/active, /studio/production/jobs/{id}
//
// Source: apps/studio_api/models/studio.py
//
// v16.5 #N carryover: regenerate via tooling/contracts/generate.py
// after Python Pydantic DTOs are added to packages/lingwen-shared.

export interface StudioProjectItemDTO {
  slug: string;
  name: string;
  role: string;
  root: string;
  location: string;
}

export interface StudioProjectsResponseDTO {
  projects: StudioProjectItemDTO[];
  active_slug?: string | null;
}

export interface StudioActiveResponseDTO {
  slug: string;
  name: string;
  root: string;
  role: string;
}

export interface StudioSetActiveRequestDTO {
  slug: string;
}

export interface StudioSummaryResponseDTO {
  slug: string;
  name: string;
  role: string;
  root: string;
  location: string;
  max_chapter: number;
  genre: string;
  chapter_count: number;
  latest_chapter: number;
  outline_count: number;
  golden_chapters: number[];
  has_golden_set: boolean;
  pilot_records_dir: string;
  pilot_record_count: number;
  pillars_ok: boolean;
  pillars_path: string;
  creation_mode?: string;
  quality_profile?: string;
}

export interface StudioQualityResponseDTO {
  slug: string;
  pillars_ok: boolean;
  pillars_path: string;
  require_chapter_outline: boolean;
  max_chapter: number;
  chapters_written: number;
  outlines_present: number;
  coverage_pct: number;
  missing_outlines: number[];
  missing_bodies: number[];
  golden_set_status: string;
  golden_regression_cmd: string;
}

export interface StudioQualityReportIssueDTO {
  severity: string;
  issue_type: string;
  chapter: number;
  description: string;
}

export interface StudioQualityReportChapterDTO {
  chapter: number;
  word_count: number;
  issue_count: number;
  issues: StudioQualityReportIssueDTO[];
}

export interface StudioProseHeatmapChapterDTO {
  chapter: number;
  issue_count: number;
  prose_p1: number;
  prose_total: number;
  structural_total: number;
  heat: number;
}

export interface StudioProseHeatmapDTO {
  chapters: StudioProseHeatmapChapterDTO[];
  max_prose_per_chapter?: number;
  total_prose_issues?: number;
  total_prose_p1?: number;
}

export interface StudioQualityReportResponseDTO {
  slug: string;
  available: boolean;
  path: string;
  total: number;
  p0: number;
  p1: number;
  p2: number;
  p3: number;
  generated_at?: string | null;
  chapters: StudioQualityReportChapterDTO[];
  prose_heatmap: StudioProseHeatmapDTO;
}

export interface StudioProseDiffTotalsDTO {
  p0?: number;
  p1?: number;
  total?: number;
  prose_p1?: number;
  prose_total?: number;
}

export interface StudioProseDiffChapterDTO {
  chapter: number;
  before_prose_p1: number;
  after_prose_p1: number;
  delta_prose_p1: number;
  before_prose_total: number;
  after_prose_total: number;
  delta_prose_total: number;
}

export interface StudioProseDiffResponseDTO {
  slug: string;
  available: boolean;
  reason?: string | null;
  snapshot_path?: string;
  report_path?: string | null;
  save_command?: string | null;
  before_captured_at?: string | null;
  after_captured_at?: string | null;
  total_delta?: StudioProseDiffTotalsDTO | null;
  chapters?: StudioProseDiffChapterDTO[];
  improved_count?: number;
  regressed_count?: number;
  has_regression?: boolean;
  net_prose_p1_delta?: number;
}

export interface StudioProseJudgeRatingDTO {
  dimension: string;
  score: number;
  evidence: string;
  action: string;
}

export interface StudioProseJudgeChapterDTO {
  chapter: number;
  avg_score: number;
  ratings: StudioProseJudgeRatingDTO[];
}

export interface StudioProseJudgeSignalDTO {
  chapter: number;
  issue_type?: string | null;
  dimension?: string | null;
  judge_score: number;
  description?: string | null;
  evidence?: string | null;
}

export interface StudioProseJudgeResponseDTO {
  slug: string;
  available: boolean;
  reason?: string | null;
  report_path?: string;
  generate_command?: string | null;
  source?: string | null;
  judged_at?: string | null;
  golden_chapters?: number[];
  weighted_avg?: number;
  chapters?: StudioProseJudgeChapterDTO[];
  high_priority_count?: number;
  false_positive_candidate_count?: number;
  review_needed_count?: number;
  high_priority?: StudioProseJudgeSignalDTO[];
  false_positive_candidates?: StudioProseJudgeSignalDTO[];
  review_needed?: StudioProseJudgeSignalDTO[];
}

export interface StudioPreflightChapterDTO {
  chapter: number;
  ok: boolean;
  message: string;
}

export interface StudioPreflightRequestDTO {
  start_chapter: number;
  end_chapter: number;
  mode?: string;
}

export interface StudioPreflightResponseDTO {
  slug: string;
  mode: string;
  start_chapter: number;
  end_chapter: number;
  all_ok: boolean;
  chapters: StudioPreflightChapterDTO[];
  batch_command: string;
}

export interface StudioBatchRunRequestDTO {
  start_chapter: number;
  end_chapter: number;
  mode?: string;
  budget_usd?: number;
  skip_preflight?: boolean;
}

export interface StudioBatchJobResponseDTO {
  job_id: string;
  slug: string;
  start_chapter: number;
  end_chapter: number;
  budget_usd: number;
  mode: string;
  status: string;
  pid?: number | null;
  log_path: string;
  started_at: string;
  finished_at?: string | null;
  exit_code?: number | null;
  error?: string | null;
  log_tail?: string | null;
}
