/**
 * useAgentTools — Agent 工具/apply/undo/cancel/annotation focus
 *
 * Phase 19 Task 6 占位：useCreatorAgent.js 564 行拆为 3 子模块之一。
 * 负责: selectCandidate + requestApply + confirmApply + cancelPlan +
 *       undoLastApply + dismissAdvice + focusAnnotation +
 *       clearPlan + resetStreamPreview + looksLikeJsonStream。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface AgentToolsDeps {
  // 暂未使用（待后续会话填充）
}

export interface AgentToolsReturn {
  pendingCandidateId: Ref<string | null>;
  streamPreview: Ref<string>;
  appliedCount: Ref<number>;
  selectCandidate: (candidateId: string) => void;
  requestApply: (candidateId: string) => void;
  confirmApply: () => void;
  cancelPlan: () => void;
  undoLastApply: () => void;
  dismissAdvice: (adviceId: string) => void;
  focusAnnotation: (annotation: Record<string, unknown>) => void;
  clearPlan: () => void;
  resetStreamPreview: () => void;
}

// 占位实现 — 后续会话填充实际逻辑
export function useAgentTools(_deps: AgentToolsDeps): AgentToolsReturn {
  throw new Error('useAgentTools: not yet implemented (Phase 19 Task 6.3)');
}