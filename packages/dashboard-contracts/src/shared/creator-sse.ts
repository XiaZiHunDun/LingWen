// Phase 126 v16.5 #N.7: typed SSE event envelope for /creator/agent/plan/stream.
//
// Source: apps/studio_api/routes/creator_core.py run_creator_agent_plan_stream
// (SSE format: `data: {json}\n\n`, JSON object shape varies by event type).
//
// Event types emitted:
//   - "start":         stream begins (no payload beyond type)
//   - "chunk":         partial plan text (incremental rendering)
//   - "advice":        LLM self-reflection on the plan
//   - "preview_label": preview label update (preview pane refresh)
//   - "done":          stream ends with final plan payload
//   - "error":         stream terminates with error
//
// The final "done" event's `plan` field is the CreatorAgentPlanResponse DTO.

import type { CreatorAgentPlanResponse } from "./creator";

export type CreatorAgentStreamEvent =
  | { type: "start"; message?: string }
  | { type: "chunk"; text: string; index?: number }
  | { type: "advice"; text: string; severity?: "info" | "warning" | "critical" }
  | { type: "preview_label"; label: string }
  | { type: "done"; plan: CreatorAgentPlanResponse }
  | { type: "error"; message: string; code?: string };

/**
 * The final return value of readCreatorAgentPlanStream — the plan object
 * embedded in the "done" event.
 */
export type CreatorAgentPlanResult = CreatorAgentPlanResponse;