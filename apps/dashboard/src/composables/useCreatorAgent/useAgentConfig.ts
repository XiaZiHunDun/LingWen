/**
 * useAgentConfig — Agent 配置/执行模式/lens/preset/director paths
 *
 * Phase 19 Task 6：从 useCreatorAgent.js 拆出（完整实现）。
 * 负责: executionMode + agentExpanded + agentLens + agentLensLabel +
 *       directorPaths + promptInput + REWRITE_LABELS + DIRECTOR_PATH_DEFS。
 *
 * 注: directorPaths 需要 currentScope + getControls() — 通过 deps 传入。
 */
import { computed, ref, watch } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { AGENT_EXECUTION_MODES, AGENT_LENS_MODES } from '../../config/creatorPanelMatrix.js';

const REWRITE_LABELS: Record<string, string> = {
  concrete: '更具体',
  dramatic: '更戏剧',
  restrained: '更克制',
  humorous: '更幽默',
  lyrical: '更抒情',
};

const DIRECTOR_PATH_DEFS = [
  { id: 'faster', label: '加快节奏', actionLabel: '加快节奏', consequence: '信息披露前移，悬念减弱但推进加快' },
  { id: 'restrained', label: '更克制', actionLabel: '更克制', consequence: '情绪降温、留白增加，适合铺垫后段' },
  { id: 'conflict', label: '升级冲突', actionLabel: '升级冲突', consequence: '对立加深，后续需安排收束与代价' },
];

interface AgentScope {
  type: 'selection' | 'chapter' | 'none';
  label: string;
  selection?: { text: string; start: number; end: number };
  chapter?: number;
}

interface AgentControls {
  styleStrength: number;
  selectionLocked: boolean;
  allowWorldbuildingFill: boolean;
  goalTag: string;
}

export interface AgentConfigDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  currentScope: ComputedRef<AgentScope>;
  getControls: () => AgentControls;
  mockAnnotations: (lens: string, actionLabel: string) => Array<Record<string, unknown>>;
  pendingPlan: Ref<Record<string, unknown> | null>;
  annotations: Ref<Array<Record<string, unknown>>>;
  generating: Ref<boolean>;
  statusLine: Ref<string>;
  executionMode: Ref<string>;
  agentLens: Ref<string>;
  agentLensLabel: ComputedRef<string>;
}

export interface AgentConfigReturn {
  executionMode: Ref<string>;
  agentExpanded: Ref<boolean>;
  promptInput: Ref<string>;
  agentLens: Ref<string>;
  agentLensLabel: ComputedRef<string>;
  directorPaths: ComputedRef<Array<Record<string, unknown>>>;
  rewritePresets: typeof REWRITE_LABELS;
  toggleExecutionMode: () => void;
  setAgentLens: (lensId: string) => void;
}

export function useAgentConfig(deps: AgentConfigDeps): AgentConfigReturn {
  const {
    currentScope,
    getControls,
    mockAnnotations,
    pendingPlan,
    annotations,
    generating,
    statusLine,
    executionMode,
    agentLens,
    agentLensLabel,
  } = deps;

  const agentExpanded = ref(false);
  const promptInput = ref('');

  const directorPaths = computed(() => {
    const scope = currentScope.value;
    if (scope.type === 'none') return [];
    const controls = getControls();
    const goal = controls.goalTag;
    return DIRECTOR_PATH_DEFS.map((path) => {
      let consequence = path.consequence;
      if (goal === 'suspense' && path.id === 'faster') consequence = '悬疑感可能减弱，建议保留 1 处未解信息';
      if (goal === 'suspense' && path.id === 'restrained') consequence = '悬疑目标下留白增加，未解信息可能更难留存';
      if (goal === 'suspense' && path.id === 'conflict') consequence = '悬疑目标下冲突升级，关键信息可能被过早暴露';
      if (goal === 'restraint' && path.id === 'conflict') consequence = '与「克制」目标冲突，冲突升级需更精准的台词';
      if (goal === 'restraint' && path.id === 'faster') consequence = '克制目标下推进加速，情绪表达可能被压缩';
      if (goal === 'pace' && path.id === 'restrained') consequence = '节奏目标下留白增多，当前节拍可能偏慢';
      if (goal === 'pace' && path.id === 'faster') consequence = '节奏目标下推进加速，段落密度可能过高';
      if (goal === 'pace' && path.id === 'conflict') consequence = '节奏目标下冲突升级，收束节拍需同步规划';
      if (goal === 'conflict' && path.id === 'faster') consequence = '冲突目标下加快披露，对抗张力可能尚未铺足';
      if (goal === 'conflict' && path.id === 'restrained') consequence = '冲突目标下情绪降温，对抗张力可能被人为压低';
      return { ...path, consequence, scopeLabel: scope.label };
    });
  });

  function toggleExecutionMode(): void {
    const isPreview = executionMode.value === AGENT_EXECUTION_MODES.preview;
    executionMode.value = isPreview ? AGENT_EXECUTION_MODES.apply : AGENT_EXECUTION_MODES.preview;
    statusLine.value = isPreview ? '执行方式：预览（A）' : '执行方式：直接应用（B2，需确认）';
  }

  function setAgentLens(lensId: string): void {
    agentLens.value = lensId;
    const plan = pendingPlan.value;
    if (plan && !plan.adviceOnly && annotations.value.length) {
      annotations.value = mockAnnotations(lensId, (plan.actionLabel as string) || '改写');
    }
    if (generating.value) {
      statusLine.value = `生成中…（${agentLensLabel.value}）`;
    }
  }

  watch(agentLens, (lens) => {
    const plan = pendingPlan.value;
    if (!plan || plan.adviceOnly) return;
    if (annotations.value.length) {
      annotations.value = mockAnnotations(lens, (plan.actionLabel as string) || '改写');
    }
  });

  return {
    executionMode,
    agentExpanded,
    promptInput,
    agentLens,
    agentLensLabel,
    directorPaths,
    rewritePresets: REWRITE_LABELS,
    toggleExecutionMode,
    setAgentLens,
  };
}