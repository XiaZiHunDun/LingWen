// Phase 126 v16.5 #7: Health DTOs (manually declared, not codegen).
//
// Wraps endpoints:
//   GET /overview, /chapters, /production-records*, /health
//
// Source: apps/studio_api/models/health.py + apps/studio_api/models/chapter.py
//   - OverviewResponse, ChaptersResponse (chapter.py)
//   - ProductionRecordsResponse, ProductionRollupResponse, ProductionCostTrendResponse (chapter.py)
//   - HealthResponse, DatabaseStatus, MemoryUsage (health.py)
//
// v16.5 #N carryover: regenerate via tooling/contracts/generate.py
// after Python Pydantic DTOs are added to packages/lingwen-shared.

export interface DatabaseStatusDTO {
  status: string;
  error?: string | null;
  tables?: number | null;
  records?: number | null;
}

export interface MemoryUsageDTO {
  rss_mb: number;
  vms_mb: number;
  cpu_percent: number;
  num_threads: number;
}

export interface HealthResponseDTO {
  status: string;
  service: string;
  timestamp: string;
  uptime: number;
  version: string;
  python_version: string;
  database: DatabaseStatusDTO;
  memory: MemoryUsageDTO;
  environment?: string | null;
  features?: Record<string, boolean> | null;
}

export interface OverviewResponseDTO {
  total_chapters: number;
  total_hooks: number;
  avg_hook_strength: number;
  total_coolpoints: number;
  avg_coolpoint_density: number;
}

export interface ChapterDataDTO {
  chapter: number;
  hook_count: number;
  hook_strength_avg: number;
  coolpoint_count: number;
  coolpoint_density: number;
}

export interface ChaptersResponseDTO {
  chapters: ChapterDataDTO[];
}

export interface ProductionRecordResponseDTO {
  record_id: string;
  record_type: string;
  chapter_num?: number | null;
  chapter_range?: string | null;
  operator?: string | null;
  recorded_at?: string | null;
  provider?: string | null;
  total_cost_usd?: number | null;
  emit_chapter_completed?: boolean | null;
  memory_context_source?: string | null;
  stopped_reason?: string | null;
  source_file: string;
}

export interface ProductionRecordsResponseDTO {
  records_dir: string;
  records: ProductionRecordResponseDTO[];
}

export interface ProductionBatchRollupResponseDTO {
  record_id: string;
  chapter_range?: string | null;
  total_cost_usd?: number | null;
  stopped_reason?: string | null;
  recorded_at?: string | null;
  source_file: string;
}

export interface ProductionRollupResponseDTO {
  records_dir: string;
  record_count: number;
  pilot_count: number;
  batch_count: number;
  total_cost_usd: number;
  chapters_with_records: number;
  latest_recorded_at?: string | null;
  batches: ProductionBatchRollupResponseDTO[];
}

export interface ProductionCostTrendPointResponseDTO {
  recorded_at?: string | null;
  record_id: string;
  record_type: string;
  label: string;
  cost_usd?: number | null;
  incremental_cost_usd: number;
  cumulative_cost_usd: number;
}

export interface ProductionCostTrendResponseDTO {
  records_dir: string;
  point_count: number;
  total_cost_usd: number;
  points: ProductionCostTrendPointResponseDTO[];
}
