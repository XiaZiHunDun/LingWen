// Phase 126 v16.5 #N.10: typed SSE event envelope for /creator/agent/plan/stream.
//
// Source: packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py
// (Pydantic source-of-truth → tooling/contracts/generate.py TS codegen → this shim).
//
// Variant interfaces (StartEvent / ChunkEvent / ... / StatusEvent) are re-exported
// from the lingwen-shared codegen output. The canonical ``CreatorAgentStreamEvent``
// discriminated union is composed from those variants to preserve TypeScript
// type narrowing on the ``type`` field.
//
// Event types emitted:
//   - "start":         stream begins (no payload beyond type)
//   - "chunk":         partial plan text (incremental rendering)
//   - "advice":        LLM self-reflection on the plan
//   - "preview_label": preview label update (preview pane refresh)
//   - "done":          stream ends with final plan payload
//   - "error":         stream terminates with error
//   - "status":        backend progress marker (Phase 126 v16.5 #N.10 promotion;
//                      emitted at packages/lingwen-creator/src/lingwen_creator/
//                      content/agent.py:534, 537, 592)
//
// The final "done" event's `plan` field is the CreatorAgentPlanResponse DTO.

import type {
  AdviceEvent as AdviceEventGenerated,
  ChunkEvent as ChunkEventGenerated,
  CreatorAgentPlanResponse,
  CreatorAgentPlanResult as CreatorAgentPlanResultGenerated,
  DoneEvent as DoneEventGenerated,
  ErrorEvent as ErrorEventGenerated,
  PreviewLabelEvent as PreviewLabelEventGenerated,
  StartEvent as StartEventGenerated,
  StatusEvent as StatusEventGenerated,
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/creator_sse';

export type StartEvent = StartEventGenerated;
export type ChunkEvent = ChunkEventGenerated;
export type AdviceEvent = AdviceEventGenerated;
export type PreviewLabelEvent = PreviewLabelEventGenerated;
export type DoneEvent = DoneEventGenerated;
export type ErrorEvent = ErrorEventGenerated;
// Phase 126 v16.5 #N.10: status variant promoted from defensive extension.
export type StatusEvent = StatusEventGenerated;

export type CreatorAgentStreamEvent =
  | StartEvent
  | ChunkEvent
  | AdviceEvent
  | PreviewLabelEvent
  | DoneEvent
  | ErrorEvent
  | StatusEvent;

/**
 * The final return value of readCreatorAgentPlanStream — the plan object
 * embedded in the "done" event.
 */
export type CreatorAgentPlanResult = CreatorAgentPlanResultGenerated;