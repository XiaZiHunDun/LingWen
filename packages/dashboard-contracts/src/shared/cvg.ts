// Phase 126 v16.5 #N.7: re-export CVG DTOs from lingwen-shared TS codegen.
import type {
  RippleListItemResponse,
  RippleDetailResponse,
  RippleActionResponse,
  RippleStatsResponse,
  RippleAuditEntryResponse,
  CascadeNodeResponse,
  CascadeEdgeResponse,
  CascadeResponse,
  CascadePreviewResponse,
  ReferenceGraphResponse,
  CascadeRunResponse,
  CascadeCancelPayload,
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/cvg';

export type RippleListItemResponseDTO = RippleListItemResponse;
export type RippleDetailResponseDTO = RippleDetailResponse;
export type RippleActionResponseDTO = RippleActionResponse;
export type RippleStatsResponseDTO = RippleStatsResponse;
export type RippleAuditEntryResponseDTO = RippleAuditEntryResponse;
export type CascadeNodeResponseDTO = CascadeNodeResponse;
export type CascadeEdgeResponseDTO = CascadeEdgeResponse;
export type CascadeResponseDTO = CascadeResponse;
export type CascadePreviewResponseDTO = CascadePreviewResponse;
export type ReferenceGraphResponseDTO = ReferenceGraphResponse;
export type CascadeRunResponseDTO = CascadeRunResponse;
export type CascadeCancelPayloadDTO = CascadeCancelPayload;
