/**
 * useAgentTools — Agent 工具（apply/undo/cancel/select/dismiss）
 *
 * Phase 19 Task 6：从 useCreatorAgent.js 拆出（完整实现）。
 * 负责: pendingPlan + candidates + directorAdvice + lastCheckpointId 状态 +
 *       selectCandidate + requestApply + confirmApply + cancelPlan + undoLastApply +
 *       dismissAdvice + focusAnnotation + hasPendingPlan computed。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';

interface AgentCandidate {
  id: string;
  label: string;
  direction?: string;
  text: string;
}

interface AgentAdvice {
  id: string;
  text: string;
}

interface AgentScope {
  type: 'selection' | 'chapter' | 'none';
  label: string;
  selection?: { text: string; start: number; end: number };
  chapter?: number;
}

interface AgentPlan {
  action: string;
  actionLabel: string;
  scope: AgentScope;
  executionMode: string;
  adviceOnly?: boolean;
  pathMeta?: unknown;
  selectedCandidateId?: string;
  confirmReplace?: boolean;
  awaitingConfirm?: boolean;
}

interface AgentControls {
  styleStrength: number;
  selectionLocked: boolean;
  allowWorldbuildingFill: boolean;
  goalTag: string;
}

export interface AgentToolsDeps {
  executionMode: Ref<string>;
  agentLensLabel: ComputedRef<string>;
  pendingPlan: Ref<AgentPlan | null>;
  candidates: Ref<AgentCandidate[]>;
  directorAdvice: Ref<AgentAdvice[]>;
  statusLine: Ref<string>;
  getControls: () => AgentControls;
  applyTextToSelection: (text: string) => void;
  createCheckpoint: (label: string) => string;
  restoreCheckpoint: (id: string) => void;
  onAnnotationFocus?: (paragraph: number) => void;
  pushMessage: (role: 'user' | 'assistant' | 'agent', text: string) => void;
  clearPlan: () => void;
}

export interface AgentToolsReturn {
  lastCheckpointId: Ref<string | null>;
  hasPendingPlan: ComputedRef<boolean>;
  selectCandidate: (candidateId: string) => void;
  requestApply: (candidateId: string) => void;
  confirmApply: () => void;
  cancelPlan: () => void;
  undoLastApply: () => void;
  dismissAdvice: (adviceId: string) => void;
  focusAnnotation: (annotation: { paragraph?: number; id?: string; level?: string; [key: string]: unknown }) => void;
}

export function useAgentTools(deps: AgentToolsDeps): AgentToolsReturn {
  const {
    executionMode,
    agentLensLabel,
    pendingPlan,
    candidates,
    directorAdvice,
    statusLine,
    getControls,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint,
    onAnnotationFocus,
    pushMessage,
    clearPlan,
  } = deps;

  const lastCheckpointId = ref<string | null>(null);

  const hasPendingPlan = computed<boolean>(() => Boolean(pendingPlan.value));

  function selectCandidate(candidateId: string): void {
    const cand = candidates.value.find((c) => c.id === candidateId);
    if (!cand) return;
    if (executionMode.value === 'preview') {
      pendingPlan.value = {
        ...(pendingPlan.value as AgentPlan),
        selectedCandidateId: candidateId,
        confirmReplace: true,
      };
      statusLine.value = `已选「${cand.label}」候选，请确认替换`;
      return;
    }
    requestApply(candidateId);
  }

  function requestApply(candidateId: string): void {
    const cand = candidates.value.find((c) => c.id === candidateId);
    if (!cand || !pendingPlan.value) return;
    pendingPlan.value = {
      ...pendingPlan.value,
      selectedCandidateId: candidateId,
      awaitingConfirm: true,
    };
    statusLine.value = '确认后将创建回滚点并替换选区';
  }

  function confirmApply(): void {
    const plan = pendingPlan.value;
    if (!plan || plan.adviceOnly) {
      statusLine.value = '只建议模式：请手动改写或提高风格强度';
      return;
    }
    const controls = getControls();
    if (controls.selectionLocked && plan.scope?.type === 'selection') {
      statusLine.value = '选区已锁定，无法应用';
      return;
    }

    const cand = candidates.value.find((c) => c.id === plan.selectedCandidateId);
    if (!cand) return;
    if (plan.scope?.type === 'none') return;

    const cpId = createCheckpoint(plan.actionLabel);
    lastCheckpointId.value = cpId;

    if (plan.scope.type === 'selection' || plan.scope.type === 'chapter') {
      applyTextToSelection(cand.text);
    }

    pushMessage('agent', `已应用「${cand.label}」· ${agentLensLabel.value} · 可撤销到版本 ${cpId.slice(0, 8)}`);
    statusLine.value = `已应用（${agentLensLabel.value}）`;
    clearPlan();
  }

  function cancelPlan(): void {
    clearPlan();
    statusLine.value = '已取消';
  }

  function undoLastApply(): void {
    if (lastCheckpointId.value) {
      restoreCheckpoint(lastCheckpointId.value);
      statusLine.value = '已恢复到上一确认点';
      pushMessage('agent', '已撤销上次应用');
    }
  }

  function dismissAdvice(adviceId: string): void {
    directorAdvice.value = directorAdvice.value.filter((a) => a.id !== adviceId);
  }

  function focusAnnotation(annotation: { paragraph?: number; id?: string; level?: string; [key: string]: unknown }): void {
    if (annotation?.paragraph && onAnnotationFocus) {
      onAnnotationFocus(annotation.paragraph);
    }
  }

  return {
    lastCheckpointId,
    hasPendingPlan,
    selectCandidate,
    requestApply,
    confirmApply,
    cancelPlan,
    undoLastApply,
    dismissAdvice,
    focusAnnotation,
  };
}
