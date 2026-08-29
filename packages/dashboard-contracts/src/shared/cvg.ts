// Phase 126 v16.5 #7: CVG (Cross-Volume Graph) DTOs (manually declared, not codegen).
//
// Wraps endpoints:
//   GET /cvg/ripples, /cvg/ripples/{id}, /cvg/ripples/stats,
//       /cvg/reference-graph, /cvg/ripples/{id}/audit,
//       /cvg/ripples/{id}/cascade, /cvg/ripples/{id}/cascade/preview,
//   POST /cvg/ripples/{id}/apply, /cvg/ripples/{id}/reject,
//        /cvg/ripples/{id}/rollback
//   GET /ripples/cascade/{id}/runs, /cascade/runs
//   POST /ripples/cascade/{id}/runs/{runId}/cancel
//   GET /ripples/cascade/{id}
//
// Source: apps/studio_api/protocols.py (Ripple*Response, Cascade*Response, ReferenceGraphResponse)
//
// v16.5 #N carryover: regenerate via tooling/contracts/generate.py
// after Python Pydantic DTOs are added to packages/lingwen-shared.

export interface RippleListItemResponseDTO {
  ripple_id: string;
  chapter_id: number;
  title: string;
  status: string;
  source_volume: number;
  impact_volumes: number[];
  created_at: string;
  updated_at?: string | null;
  proposed_by?: string;
  applies_count?: number;
}

export interface RippleDetailResponseDTO extends RippleListItemResponseDTO {
  description?: string;
  evidence?: Record<string, unknown>;
  references?: Record<string, unknown>[];
  apply_metadata?: Record<string, unknown>;
  audit_trail?: RippleAuditEntryResponseDTO[];
}

export interface RippleActionResponseDTO {
  ripple_id: string;
  action: string;
  status: string;
  applied_at?: string | null;
  rejected_at?: string | null;
  reason?: string | null;
  message?: string;
}

export interface RippleStatsResponseDTO {
  total: number;
  pending: number;
  applied: number;
  rejected: number;
  rolled_back: number;
  by_status?: Record<string, number>;
  by_volume?: Record<string, number>;
}

export interface RippleAuditEntryResponseDTO {
  audit_id: string;
  ripple_id: string;
  action: string;
  actor: string;
  timestamp: string;
  reason?: string | null;
  metadata?: Record<string, unknown>;
}

export interface CascadeNodeResponseDTO {
  node_id: string;
  chapter_id: number;
  title: string;
  status: string;
  depth: number;
}

export interface CascadeEdgeResponseDTO {
  source: string;
  target: string;
  relation: string;
  weight?: number;
}

export interface CascadeResponseDTO {
  ripple_id: string;
  nodes: CascadeNodeResponseDTO[];
  edges: CascadeEdgeResponseDTO[];
  total_nodes: number;
  total_edges: number;
  max_depth: number;
  status?: string;
}

export interface CascadePreviewResponseDTO {
  ripple_id: string;
  estimated_impact: number;
  affected_chapters: number[];
  preview_tree?: CascadeResponseDTO;
  warnings?: string[];
}

export interface ReferenceGraphResponseDTO {
  nodes: Record<string, unknown>[];
  edges: Record<string, unknown>[];
  total_nodes: number;
  total_edges: number;
  by_dimension?: Record<string, number>;
}

export interface CascadeRunResponseDTO {
  run_id: string;
  ripple_id: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
  nodes_processed: number;
  max_depth: number;
  algorithm?: string;
  metadata?: Record<string, unknown>;
}

export interface CascadeCancelPayloadDTO {
  run_id: string;
  cancelled_at?: string | null;
  reason?: string | null;
}
