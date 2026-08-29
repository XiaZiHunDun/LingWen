// Phase 126 v16.5 #7: Decisions DTOs (manually declared, not codegen).
//
// Wraps endpoints:
//   GET /decisions/pending, /decisions/all
//   POST /decisions/{id}/resolve, /decisions/{id}/defer, /decisions/{id}/cancel
//
// Source: apps/studio_api/models/decision.py
//
// v16.5 #N carryover: regenerate via tooling/contracts/generate.py
// after Python Pydantic DTOs are added to packages/lingwen-shared.

export interface DecisionResponseDTO {
  decision_id: string;
  kind: string;
  node_id: string;
  prompt: string;
  options: string[];
  priority: number;
  status: string;
  context?: Record<string, unknown>;
  created_at?: string | null;
  resolution?: string | null;
  resolved_at?: string | null;
  resolved_by?: string | null;
  reason?: string | null;
}

export interface ResolveDecisionRequestDTO {
  option: string;
  resolved_by?: string;
}

export interface DeferDecisionRequestDTO {
  reason?: string;
}

export interface CancelDecisionRequestDTO {
  reason?: string;
}
