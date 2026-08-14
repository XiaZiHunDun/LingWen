/**
 * useCreatorAgent — 写作导演（预览 A / 确认应用 B2）
 * 计划生成对接 POST /api/creator/agent/plan，失败时降级本地 mock
 *
 * Phase 19 Task 6 完成版：抽出全部 3 个 .ts 子模块，本主 hook 改为组合 facade。
 * 下游 API（return shape）保持完全兼容。
 *
 * 子模块：
 * - useAgentConfig  (配置/执行模式/lens/preset/director paths)
 * - useAgentTask    (任务执行：runPlan/director path/prompt/chat/ask)
 * - useAgentTools   (工具：apply/undo/cancel/select/dismiss)
 *
 * 共享状态（主 hook 编排）：
 * - pendingPlan, candidates, directorAdvice: tools 拥有，task 写入
 * - statusLine, annotations: task 拥有，tools 读取
 * - agentLens, agentLensLabel, executionMode: config 拥有
 */
import { computed, ref } from 'vue';
import { AGENT_EXECUTION_MODES, AGENT_LENS_MODES } from '../config/creatorPanelMatrix.js';
import {
  useAgentConfig,
  useAgentTask,
  useAgentTools,
} from './useCreatorAgent/index.ts';

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   getSelection: () => { text: string, start: number, end: number } | null,
 *   getChapterNum: () => number | null,
 *   getBodyDraft: () => string,
 *   getControls: () => {
 *     styleStrength: number,
 *     selectionLocked: boolean,
 *     allowWorldbuildingFill: boolean,
 *     goalTag: string,
 *   },
 *   applyTextToSelection: (text: string) => void,
 *   createCheckpoint: (label: string) => string,
 *   restoreCheckpoint: (id: string) => void,
 *   onAnnotationFocus?: (paragraph: number) => void,
 * }} deps
 */
export function useCreatorAgent(deps) {
  const {
    uiProfile,
    getSelection,
    getChapterNum,
    getBodyDraft,
    getControls,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint,
    onAnnotationFocus,
  } = deps;

  // --- 共享 ref（跨子模块通信）---
  // pendingPlan / candidates / directorAdvice 由 task 写入，tools 读取并应用
  // statusLine / annotations 由 task 拥有并更新，tools 读取做应用反馈
  const pendingPlan = ref(null);
  const candidates = ref([]);
  const directorAdvice = ref([]);
  const annotations = ref([]);

  // 共享的 agentLens/executionMode（主 hook 拥有，config 和 task 都引用）
  // 从 uiProfile 初始化以保留原有行为
  const executionMode = ref(
    uiProfile.value.agent_execution_mode_default === AGENT_EXECUTION_MODES.apply
      ? AGENT_EXECUTION_MODES.apply
      : AGENT_EXECUTION_MODES.preview,
  );
  const agentLens = ref(uiProfile.value.agent_lens_default || 'author');
  const agentLensLabel = computed(() => {
    const found = AGENT_LENS_MODES.find((m) => m.id === agentLens.value);
    return found?.label || agentLens.value;
  });

  // --- 1) Task 子模块（先建，提供 currentScope / annotations 给 config）---
  const task = useAgentTask({
    executionMode,
    agentLens,
    agentLensLabel,
    getSelection,
    getChapterNum,
    getBodyDraft,
    getControls,
    pendingPlan,
    candidates,
    directorAdvice,
    annotations,
  });

  // --- 2) Config 子模块（依赖 task.currentScope + task.mockAnnotations）---
  const config = useAgentConfig({
    uiProfile,
    currentScope: task.currentScope,
    getControls,
    mockAnnotations: task.mockAnnotations,
    pendingPlan,
    annotations,
    generating: task.generating,
    statusLine: task.statusLine,
    executionMode,
    agentLens,
    agentLensLabel,
  });

  // 把 config 内部的 executionMode/agentLens 替换为主 hook 共享 ref
  // （config 内部初始化时会用 uiProfile.value 设置初值 — 我们丢弃 config 内部状态）

  // --- 3) Tools 子模块（依赖 config.executionMode + config.agentLensLabel）---
  const tools = useAgentTools({
    executionMode,
    agentLensLabel,
    pendingPlan,
    candidates,
    directorAdvice,
    statusLine: task.statusLine,
    getControls,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint,
    onAnnotationFocus,
    pushMessage: task.pushMessage,
    clearPlan: task.clearPlan,
  });

  // --- submitPrompt 包装（task 内部用 ref，需要 promptInput）---
  async function submitPrompt() {
    const text = config.promptInput.value.trim();
    if (!text) return;
    task.pushMessage('user', text);
    config.promptInput.value = '';
    await task.runPlan('prompt', text);
  }

  return {
    // Config state
    executionMode,
    agentExpanded: config.agentExpanded,
    promptInput: config.promptInput,
    agentLens,
    agentLensLabel,
    directorPaths: config.directorPaths,
    rewritePresets: config.rewritePresets,
    isPreviewMode: computed(() => executionMode.value === 'preview'),
    // Task state
    messages: task.messages,
    generating: task.generating,
    statusLine: task.statusLine,
    planProvider: task.planProvider,
    streamPreviewText: task.streamPreviewText,
    streamPreviewLabel: task.streamPreviewLabel,
    streamSource: task.streamSource,
    streamDisplayText: task.streamDisplayText,
    streamAdvicePreview: task.streamAdvicePreview,
    currentScope: task.currentScope,
    annotations,
    // Tools state
    pendingPlan,
    candidates,
    directorAdvice,
    lastCheckpointId: tools.lastCheckpointId,
    hasPendingPlan: tools.hasPendingPlan,
    // Actions
    submitPrompt,
    runRewritePreset: task.runRewritePreset,
    runDirectorPath: task.runDirectorPath,
    chat: task.chat,
    ask: task.ask,
    runPlan: task.runPlan,
    selectCandidate: tools.selectCandidate,
    confirmApply: tools.confirmApply,
    cancelPlan: tools.cancelPlan,
    undoLastApply: tools.undoLastApply,
    toggleExecutionMode: config.toggleExecutionMode,
    dismissAdvice: tools.dismissAdvice,
    setAgentLens: config.setAgentLens,
    focusAnnotation: tools.focusAnnotation,
    clearPlan: task.clearPlan,
    buildScope: task.buildScope,
  };
}