/**
 * useCreatorWrite — 写栏章节预览与内嵌编辑（从 CreatorPage 抽出）
 *
 * Phase 19 Task 5 完成版：抽出全部 3 个 .ts 子模块，本主 hook 改为组合 facade。
 * 下游 API（panelContext shape）保持完全兼容。
 *
 * 子模块：
 * - useWriteFlow       (写作流：选章节/保存/自动保存/记忆同步)
 * - useWriteValidation (写作验证：P0 复检/逻辑检查点击/偏离点击 — 类型骨架占位)
 * - useWriteTools      (写作工具：format/label/class/highlight/batch inline)
 */
import { computed, nextTick, onUnmounted, ref, watch } from 'vue';
import { useCreatorWriteWorkbench } from './useCreatorWriteWorkbench.js';
import { extractMentionedEntityNames } from '../utils/creatorChapterEntityUtils.js';
import {
  useWriteFlow,
  useWriteTools,
} from './useCreatorWrite/index.ts';

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   handleSaveError: (err: unknown) => void,
 *   onAfterChapterSave: () => Promise<void>,
 *   isWorkspaceColumnVisible: (col: string) => boolean,
 *   workspaceTabsEnabled: import('vue').ComputedRef<boolean>,
 *   visibleDeviations: import('vue').ComputedRef<object[]>,
 *   deviationHighlightEnabled: import('vue').ComputedRef<boolean>,
 *   highlightedDeviationChapter: import('vue').Ref<number|null>,
 *   logicCheckRunning: import('vue').Ref<boolean>,
 *   logicCheckResult: import('vue').Ref<object|null>,
 *   runCompanionLogicCheck: () => Promise<void>,
 *   openVolumeSummaryForRange: (start: number, end: number) => void,
 *   focusChapter?: import('vue').Ref<number|null>,
 * } deps
 */
export function useCreatorWrite(deps) {
  const {
    uiProfile, overview, error, saveMessage, handleSaveError, onAfterChapterSave,
    isWorkspaceColumnVisible, workspaceTabsEnabled, visibleDeviations,
    deviationHighlightEnabled, highlightedDeviationChapter,
    logicCheckRunning, logicCheckResult, runCompanionLogicCheck,
    openVolumeSummaryForRange, focusChapter,
  } = deps;

  // --- 共享 ref（主 hook 拥有，子模块通过 deps 接收）---
  const selectedChapter = ref(null);
  const chapterPreview = ref(null);
  const chapterBodyDraft = ref('');
  const chapterOutlineDraft = ref('');
  const chapterBodySaving = ref(false);
  const chapterOutlineSaving = ref(false);
  const chapterBodyTextareaRef = ref(null);
  const bodyLastSavedAt = ref(null);
  const bodyAutoSaveStatus = ref('idle');
  const lastPersistedBody = ref('');
  let autoSaveTimer = null;
  const chapterBodyHighlightActive = ref(false);
  const activeRecheckIssueIdx = ref(null);
  const activeLogicCheckIssueIdx = ref(null);
  const chapterRecheckResult = ref(null);
  const previewLoading = ref(false);
  const batchDeviationInlineSummary = ref(null);
  let chapterBodyHighlightTimer = null;
  let logicCheckIssueHighlightTimer = null;
  let deviationHighlightTimer = null;

  // --- Workbench（保持原状，不重构）---
  const memoryAssetsCache = ref([]);
  function syncMemoryAssets(items) {
    memoryAssetsCache.value = Array.isArray(items) ? items : [];
  }
  const wb = useCreatorWriteWorkbench({
    uiProfile,
    overview,
    chapterBodyDraft,
    selectedChapter,
    saveMessage,
    logicCheckResult,
    visibleDeviations,
    memoryAssets: memoryAssetsCache,
    getMemoryAssets: () => memoryAssetsCache.value,
    focusParagraphByIndex: (paragraph, source = 'inline') => {
      tools.focusIssueParagraph({ paragraph }, null, source);
    },
  });
  watch(logicCheckResult, (result) => {
    wb.syncQualityFromLogicCheck(result);
  });

  // --- 1) WriteTools 子模块（先建，提供 focusIssueParagraph 给 validation）---
  const tools = useWriteTools({
    uiProfile,
    chapterBodyDraft,
    chapterBodyTextareaRef,
    chapterBodyHighlightActiveRef: chapterBodyHighlightActive,
    chapterBodyHighlightTimerRef: { get value() { return chapterBodyHighlightTimer; }, set value(v) { chapterBodyHighlightTimer = v; } },
    batchDeviationInlineSummary,
    visibleDeviations,
    overview,
    activeRecheckIssueIdxRef: activeRecheckIssueIdx,
    jumpToChapter: async (ch) => { await flow.selectChapter(ch); },
    openVolumeSummaryForRange,
  });

  // --- 2) WriteFlow 子模块 ---
  const flow = useWriteFlow({
    uiProfile,
    overview,
    error,
    saveMessage,
    handleSaveError,
    onAfterChapterSave,
    selectedChapter,
    chapterPreview,
    chapterBodyDraft,
    chapterOutlineDraft,
    chapterBodySaving,
    chapterOutlineSaving,
    chapterBodyTextareaRef,
    bodyLastSavedAt,
    bodyAutoSaveStatus,
    chapterRecheckResult,
    previewLoading,
    focusChapter,
    memoryAssetsCache,
    lastPersistedBodyRef: lastPersistedBody,
  });

  // --- Validation 子模块（类型骨架，抛错 — 主 hook 内部保留原实现）---
  // 不接入子模块，直接在主 hook 内部定义（与原代码一致）
  async function recheckChapterP0(chapter) {
    try {
      const { runCreatorLogicCheck } = await import('../api/index.js');
      const result = await runCreatorLogicCheck({ chapter, scope: 'p0' });
      chapterRecheckResult.value = result;
      activeRecheckIssueIdx.value = null;
    } catch (e) {
      handleSaveError(e);
    }
  }

  function pulseLogicCheckIssueHighlight(issueIdx) {
    activeLogicCheckIssueIdx.value = issueIdx;
    if (logicCheckIssueHighlightTimer) clearTimeout(logicCheckIssueHighlightTimer);
    logicCheckIssueHighlightTimer = setTimeout(() => {
      activeLogicCheckIssueIdx.value = null;
    }, 1500);
  }

  function pulseDeviationHighlight(chapter) {
    highlightedDeviationChapter.value = chapter;
    if (deviationHighlightTimer) clearTimeout(deviationHighlightTimer);
    deviationHighlightTimer = setTimeout(() => {
      highlightedDeviationChapter.value = null;
    }, 1500);
  }

  async function handleLogicCheckIssueClick(issue, idx) {
    activeLogicCheckIssueIdx.value = idx;
    if (selectedChapter.value != null) {
      await tools.focusIssueParagraph(issue, idx, 'logic');
    }
    pulseLogicCheckIssueHighlight(idx);
  }

  async function handleDeviationClick(deviation) {
    const chapter = Number(deviation.chapter);
    if (Number.isFinite(chapter) && chapter > 0) {
      highlightedDeviationChapter.value = chapter;
      if (deviationHighlightEnabled.value) pulseDeviationHighlight(chapter);
    }
  }

  function onRecheckIssueKeydown(event, issue, idx) {
    const key = event.key;
    if (key === 'Enter' || key === ' ') {
      event.preventDefault();
      activeRecheckIssueIdx.value = idx;
      void tools.focusIssueParagraph(issue, idx, 'recheck');
    }
  }

  function onLogicCheckIssueKeydown(event, issue, idx) {
    const key = event.key;
    if (key === 'Enter' || key === ' ') {
      event.preventDefault();
      void handleLogicCheckIssueClick(issue, idx);
    }
  }

  // --- 同步 workbench 的 wb.bindChapterBodyTextareaRef ---
  function bindChapterBodyTextareaRef(el) {
    flow.bindChapterBodyTextareaRef(el);
    // 同时通知 workbench
    wb.bindChapterBodyTextareaRef?.(el);
  }

  // --- formatBodySaveTime / bodySaveStatusLabel / watch chapterBodyDraft（保持原状）---
  function formatBodySaveTime(date) {
    if (!date) return '';
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  }

  const bodySaveStatusLabel = computed(() => {
    if (chapterBodySaving.value || bodyAutoSaveStatus.value === 'saving') return '保存中…';
    if (bodyAutoSaveStatus.value === 'error') return '自动保存失败，请手动保存';
    if (bodyLastSavedAt.value) return `已自动保存 · ${formatBodySaveTime(bodyLastSavedAt.value)}`;
    if (bodyAutoSaveStatus.value === 'pending') return '编辑中…';
    if (
      selectedChapter.value
      && uiProfile.value.chapter_inline_edit
      && !previewLoading.value
    ) {
      return '输入后自动保存';
    }
    return '';
  });

  watch(chapterBodyDraft, (draft) => {
    if (!uiProfile.value.chapter_inline_edit) return;
    if (!selectedChapter.value || previewLoading.value) return;
    if (draft === lastPersistedBody.value) {
      bodyAutoSaveStatus.value = bodyLastSavedAt.value ? 'saved' : 'idle';
      return;
    }
    bodyAutoSaveStatus.value = 'pending';
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
      flow.autoSaveChapterBody();
    }, 2000);
  });

  function maybeAutoSelectWritingChapter() {
    if (!workspaceTabsEnabled.value || selectedChapter.value) return;
    const ov = overview.value;
    if (!ov || (ov.creation_mode !== 'companion' && ov.creation_mode !== 'advance')) return;
    const chapters = ov.chapters || [];
    const focus = focusChapter?.value;
    if (focus != null && chapters.some((ch) => ch.chapter === focus)) {
      flow.selectChapter(focus);
      return;
    }
    const target = chapters.find((ch) => !ch.has_body) || chapters[0];
    if (target?.chapter) {
      flow.selectChapter(target.chapter);
    }
  }

  function jumpToChapter(chapter) {
    return flow.selectChapter(chapter);
  }

  onUnmounted(() => {
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
  });

  // --- 暴露 wb 的 quickActions 等（保持原 workbench 接口）---
  const panelContext = {
    uiProfile,
    selectedChapter,
    chapterPreview,
    chapterBodyDraft,
    chapterOutlineDraft,
    chapterBodySaving,
    chapterOutlineSaving,
    chapterBodyTextareaRef,
    bodyLastSavedAt,
    bodyAutoSaveStatus,
    chapterRecheckResult,
    previewLoading,
    activeRecheckIssueIdx,
    activeLogicCheckIssueIdx,
    chapterBodyHighlightActive,
    batchDeviationInlineSummary,
    deviationChapters: flow.deviationChapters,
    alertChapters: flow.alertChapters,
    visibleChapters: flow.visibleChapters,
    showCompanionLogicCheckInWrite: flow.showCompanionLogicCheckInWrite,
    syncMemoryAssets,
    selectChapter: flow.selectChapter,
    jumpToChapter,
    saveChapterBody: flow.saveChapterBody,
    saveChapterOutline: flow.saveChapterOutline,
    autoSaveChapterBody: flow.autoSaveChapterBody,
    bindChapterBodyTextareaRef,
    maybeAutoSelectWritingChapter,
    recheckChapterP0,
    handleLogicCheckIssueClick,
    handleDeviationClick,
    onRecheckIssueKeydown,
    onLogicCheckIssueKeydown,
    pulseLogicCheckIssueHighlight,
    pulseDeviationHighlight,
    formatBodySaveTime,
    bodySaveStatusLabel,
    chapterRowClass: tools.chapterRowClass,
    chapterVolumeLabel: tools.chapterVolumeLabel,
    chapterRowTitle: tools.chapterRowTitle,
    pulseChapterBodyHighlight: tools.pulseChapterBodyHighlight,
    focusIssueParagraph: tools.focusIssueParagraph,
    batchDeviationsInRange: tools.batchDeviationsInRange,
    scrollToBatchDeviationList: tools.scrollToBatchDeviationList,
    openFirstBatchDeviationChapter: tools.openFirstBatchDeviationChapter,
    updateBatchDeviationInlineSummary: tools.updateBatchDeviationInlineSummary,
    linkBatchDeviationInlineSummary: tools.linkBatchDeviationInlineSummary,
    dismissBatchDeviationInlineSummary: tools.dismissBatchDeviationInlineSummary,
    navigateIssueList: tools.navigateIssueList,
    isWorkspaceColumnVisible,
    workspaceTabsEnabled,
    // wb 暴露
    wb,
  };

  return {
    panelContext,
    syncMemoryAssets,
    selectedChapter,
    maybeAutoSelectWritingChapter,
    updateBatchDeviationInlineSummary: tools.updateBatchDeviationInlineSummary,
    dismissBatchDeviationInlineSummary: tools.dismissBatchDeviationInlineSummary,
    focusIssueParagraph: tools.focusIssueParagraph,
  };
}