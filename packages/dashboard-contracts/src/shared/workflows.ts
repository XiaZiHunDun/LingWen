// Phase 126 v16.5 #N.7: re-export Workflows DTOs from lingwen-shared TS codegen.
import type {
  WorkflowListItem,
  RunWorkflowRequest,
  ResumeWorkflowRequest,
  WorkflowStatusResponse,
  WorkflowMermaidResponse,
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/workflows';

export type WorkflowListItemDTO = WorkflowListItem;
export type RunWorkflowRequestDTO = RunWorkflowRequest;
export type ResumeWorkflowRequestDTO = ResumeWorkflowRequest;
export type WorkflowStatusResponseDTO = WorkflowStatusResponse;
export type WorkflowMermaidResponseDTO = WorkflowMermaidResponse;
