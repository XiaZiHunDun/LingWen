/**
 * useCreatorWriteWorkbench — facade (Phase 60 重构)
 *
 * 把 529L 单文件实现拆为 4 个 .ts 子模块（Layout/Selection/Checkpoints/Quality），
 * facade 负责：
 * 1. 创建/持有 shared refs（已在 deps 中）
 * 2. 调用 4 个子模块，注入 deps
 * 3. 聚合返回值，保持对外 55 字段接口零变化
 * 4. 维护跨子模块 computeds（showInlineConflictGutter）
 * 5. 创建 agent 并注入到 Quality 子模块
 */
import { computed } from 'vue';
import { useCreatorAgent } from './useCreatorAgent.js';
import {
  useWorkbenchLayout,
  useWorkbenchSelection,
  useWorkbenchCheckpoints,
  useWorkbenchQuality,
} from './useCreatorWriteWorkbench/index.js';

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   chapterBodyDraft: import('vue').Ref<string>,
 *   selectedChapter: import('vue').Ref<number|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   logicCheckResult?: import('vue').Ref<object|null>,
 *   visibleDeviations?: import('vue').ComputedRef<object[]>,
 *   getMemoryAssets?: () => object[],
 *   memoryAssets?: import('vue').Ref<object[]>,
 *   focusParagraphByIndex?: (paragraph: number, source?: string) => void,
 * }} deps
 */
export function useCreatorWriteWorkbench(deps) {
  const {
    uiProfile,
    overview,
    chapterBodyDraft,
    selectedChapter,
    saveMessage,
    logicCheckResult,
    visibleDeviations,
    getMemoryAssets = () => [],
    memoryAssets,
    focusParagraphByIndex,
  } = deps;

  // ── Selection 子模块（先创建，qualityHints 需被 Quality 共享）──
  const selection = useWorkbenchSelection({
    chapterBodyDraft,
    saveMessage,
  });

  // ── Checkpoints 子模块 ──
  const checkpoints = useWorkbenchCheckpoints({
    selectedChapter,
    chapterBodyDraft,
    saveMessage,
  });

  // ── Layout 子模块（需要 isPanelVisible 给 Quality 用）──
  const layout = useWorkbenchLayout({
    uiProfile,
    overview,
    selectedChapter,
    chapterBodyDraft,
    memoryAssets,
    getMemoryAssets,
    logicCheckResult,
    visibleDeviations,
  });

  // ── 创建 agent（主 hook 持有）──
  const agent = useCreatorAgent({
    uiProfile,
    getSelection: () => selection.bodySelection.value,
    getChapterNum: () => selectedChapter.value,
    getBodyDraft: () => chapterBodyDraft.value,
    getControls: selection.getControls,
    applyTextToSelection: selection.applyTextToSelection,
    createCheckpoint: checkpoints.createCheckpoint,
    restoreCheckpoint: (id) => checkpoints.restoreCheckpoint(id),
    onAnnotationFocus: (paragraph) => {
      if (focusParagraphByIndex) focusParagraphByIndex(paragraph, 'inline');
    },
  });

  // ── Quality 子模块（依赖 layout.isPanelVisible + agent）──
  const quality = useWorkbenchQuality({
    selectedChapter,
    chapterBodyDraft,
    visibleDeviations,
    logicCheckResult,
    selectionQualityHints: selection.qualityHints,
    overview,
    isPanelVisible: layout.isPanelVisible,
    getAgent: () => agent,
    focusParagraphByIndex,
  });

  // ── 跨子模块 computed ──
  const showInlineConflictGutter = computed(() =>
    layout.isPanelVisible('inlineConflictGutter') && quality.inlineConflictMarkers.value.length > 0,
  );

  return {
    // ── Layout (12 fields) ──
    workbenchEnabled: layout.workbenchEnabled,
    leftPanelCollapsed: layout.leftPanelCollapsed,
    humanFirstDesk: layout.humanFirstDesk,
    goalCardLines: layout.goalCardLines,
    consistencyItems: layout.consistencyItems,
    consistencyPanelOpen: layout.consistencyPanelOpen,
    chapterEntities: layout.chapterEntities,
    isPanelVisible: layout.isPanelVisible,
    isPanelCollapsed: layout.isPanelCollapsed,
    isLeftRailPanelVisible: layout.isLeftRailPanelVisible,
    creationMode: layout.creationMode,
    updateCreationMode: layout.updateCreationMode,

    // ── Selection (10 fields) ──
    bodySelection: selection.bodySelection,
    hasBodySelection: selection.hasBodySelection,
    styleStrength: selection.styleStrength,
    selectionLocked: selection.selectionLocked,
    allowWorldbuildingFill: selection.allowWorldbuildingFill,
    goalTag: selection.goalTag,
    captureBodySelection: selection.captureBodySelection,
    applyTextToSelection: selection.applyTextToSelection,
    toggleSelectionLock: selection.toggleSelectionLock,
    getControls: selection.getControls,

    // ── Checkpoints (7 fields) ──
    checkpoints: checkpoints.checkpoints,
    diffCheckpointId: checkpoints.diffCheckpointId,
    diffView: checkpoints.diffView,
    createCheckpoint: checkpoints.createCheckpoint,
    restoreCheckpoint: checkpoints.restoreCheckpoint,
    openCheckpointDiff: checkpoints.openCheckpointDiff,
    closeCheckpointDiff: checkpoints.closeCheckpointDiff,

    // ── Quality (24 fields: intent + validation + hints + conflicts + generation) ──
    intentText: quality.intentText,
    intentGenre: quality.intentGenre,
    intentMood: quality.intentMood,
    intentType: quality.intentType,
    intentTheme: quality.intentTheme,
    intentHistory: quality.intentHistory,
    saveIntentToHistory: quality.saveIntentToHistory,
    loadIntentFromHistory: quality.loadIntentFromHistory,
    clearIntentHistory: quality.clearIntentHistory,
    qualityHints: selection.qualityHints, // shared ref from Selection (Quality writes to it)
    dismissQualityHint: quality.dismissQualityHint,
    syncQualityFromLightValidation: quality.syncQualityFromLightValidation,
    syncQualityFromLogicCheck: quality.syncQualityFromLogicCheck,
    lightValidationIssues: quality.lightValidationIssues,
    lightValidationSummary: quality.lightValidationSummary,
    lightValidationRunning: quality.lightValidationRunning,
    runLightValidationNow: quality.runLightValidationNow,
    scheduleLightValidation: quality.scheduleLightValidation,
    inlineConflictMarkers: quality.inlineConflictMarkers,
    activeInlineConflictId: quality.activeInlineConflictId,
    chapterBodyConflictHighlightActive: quality.chapterBodyConflictHighlightActive,
    focusInlineConflict: quality.focusInlineConflict,
    focusLightValidationIssue: quality.focusLightValidationIssue,
    clearInlineConflictFocus: quality.clearInlineConflictFocus,
    generateIntensity: quality.generateIntensity,
    generateRunning: quality.generateRunning,
    startQuickWrite: quality.startQuickWrite,
    stopGenerate: quality.stopGenerate,

    // ── Cross-submodule computed (1 field) ──
    showInlineConflictGutter,

    // ── Agent (1 field) ──
    agent,
  };
}
