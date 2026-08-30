// Phase 126 v16.5 #N.7: re-export Decisions DTOs from lingwen-shared TS codegen.
import type {
  DecisionResponse,
  ResolveDecisionRequest,
  DeferDecisionRequest,
  CancelDecisionRequest,
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/decisions';

export type DecisionResponseDTO = DecisionResponse;
export type ResolveDecisionRequestDTO = ResolveDecisionRequest;
export type DeferDecisionRequestDTO = DeferDecisionRequest;
export type CancelDecisionRequestDTO = CancelDecisionRequest;
