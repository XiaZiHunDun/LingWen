/**
 * useCreatorWriteWorkbench — 左栈工作台状态、选区、checkpoint、导演控制（Human Comfort P0）
 */
import { computed, ref } from 'vue';
import {
  isWriteWorkbenchLayoutEnabled,
  isWriteWorkbenchPanelVisible,
  isHumanFirstDeskMode,
  isPanelDefaultCollapsed,
  CREATOR_WRITE_WORKBENCH_MATRIX,
} from '../config/creatorPanelMatrix.js';
import { computeLineDiff, countDiffChanges } from '../utils/textDiffUtils.js';
import { resolveChapterEntities } from '../utils/creatorChapterEntityUtils.js';
import { buildInlineConflictMarkers } from '../utils/creatorInlineConflictUtils.js';
import { useCreatorAgent } from './useCreatorAgent.js';
import { useEffectiveCreationMode } from './useEffectiveCreationMode.js';

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
    focusParagraphByIndex,
  } = deps;

  const leftPanelCollapsed = ref(false);
  const intentText = ref('');
  const intentGenre = ref('');
  const intentMood = ref('');
  const bodySelection = ref({ start: 0, end: 0, text: '' });
  const checkpoints = ref([]);
  const qualityHints = ref([]);
  const generateIntensity = ref('balanced');
  const generateRunning = ref(false);

  const styleStrength = ref(1);
  const selectionLocked = ref(false);
  const allowWorldbuildingFill = ref(false);
  const goalTag = ref('');

  const diffCheckpointId = ref(null);
  const activeInlineConflictId = ref(null);
  const chapterBodyConflictHighlightActive = ref(false);
  let inlineConflictHighlightTimer = null;

  const creationMode = useEffectiveCreationMode(
    computed(() => overview.value?.creation_mode ?? 'companion'),
    computed(() => (overview.value
      ? { slug: overview.value.slug, name: overview.value.name }
      : null)),
  );

  const workbenchEnabled = computed(() =>
    isWriteWorkbenchLayoutEnabled(creationMode.value, uiProfile.value),
  );

  const humanFirstDesk = computed(() => isHumanFirstDeskMode(creationMode.value));

  function isPanelVisible(panelId) {
    if (panelId === 'inlineConflictGutter' && uiProfile.value.write_inline_conflict_gutter === false) {
      return false;
    }
    if (panelId === 'chapterEntityRail' && uiProfile.value.write_chapter_entity_rail === false) {
      return false;
    }
    return isWriteWorkbenchPanelVisible(creationMode.value, panelId);
  }

  function isPanelCollapsed(panelId) {
    return isPanelDefaultCollapsed(CREATOR_WRITE_WORKBENCH_MATRIX, creationMode.value, panelId);
  }

  const chapterEntities = computed(() =>
    resolveChapterEntities({
      memoryAssets: getMemoryAssets(),
      chapter: selectedChapter.value,
      bodyText: chapterBodyDraft.value,
    }),
  );

  const inlineConflictMarkers = computed(() =>
    buildInlineConflictMarkers({
      chapter: selectedChapter.value,
      deviations: visibleDeviations?.value || overview.value?.deviations || [],
      logicIssues: logicCheckResult?.value?.issues || [],
    }),
  );

  const showInlineConflictGutter = computed(
    () => isPanelVisible('inlineConflictGutter') && inlineConflictMarkers.value.length > 0,
  );

  const hasBodySelection = computed(() => Boolean(bodySelection.value.text?.trim()));

  const goalCardLines = computed(() => {
    const ov = overview.value;
    const mode = creationMode.value;
    if (mode === 'companion') {
      return {
        line1: ov?.name || '当前项目',
        line2: '陪写本章，你来定稿',
        line3: '选一条路径 → 预览 → 确认落字',
      };
    }
    if (mode === 'advance') {
      return {
        line1: ov?.name || '当前项目',
        line2: '按卷纲推进，一章一章写',
        line3: '你定方向，系统辅助产章与校对',
      };
    }
    return { line1: ov?.name || '当前项目', line2: '工厂模式', line3: '产线调度' };
  });

  const consistencyItems = computed(() => {
    const ch = selectedChapter.value;
    const items = [];
    const deviations = (overview.value?.deviations || [])
      .filter((d) => !ch || d.chapter === ch)
      .slice(0, 2);
    for (const d of deviations) {
      items.push({
        id: `dev-${d.chapter}-${d.message}`,
        level: d.severity === 'alert' ? 'warn' : 'info',
        text: d.chapter ? `ch${String(d.chapter).padStart(3, '0')} · ${d.message}` : d.message,
        kind: 'deviation',
      });
    }
    const issues = logicCheckResult?.value?.issues || [];
    for (const issue of issues.slice(0, 2)) {
      if (ch && issue.chapter && issue.chapter !== ch) continue;
      items.push({
        id: `lc-${issue.title || issue.message}`,
        level: issue.severity === 'P0' ? 'warn' : 'info',
        text: issue.title || issue.message,
        kind: 'logic',
      });
    }
    if (!items.length && ch && !humanFirstDesk.value) {
      items.push({
        id: 'mem-ok',
        level: 'ok',
        text: `ch${String(ch).padStart(3, '0')} 暂无冲突标记`,
        kind: 'memory',
      });
    }
    return items.slice(0, 3);
  });

  const consistencyPanelOpen = computed(() => {
    if (humanFirstDesk.value) {
      return consistencyItems.value.some((i) => i.level === 'warn');
    }
    if (consistencyItems.value.some((i) => i.level === 'warn')) return true;
    return !isPanelCollapsed('consistencyRail');
  });

  /** 伴侣书桌左栏：仅章节列表，其余收进主区工具 */
  function isLeftRailPanelVisible(panelId) {
    if (!humanFirstDesk.value) return isPanelVisible(panelId);
    return false;
  }

  const diffView = computed(() => {
    const cp = checkpoints.value.find((c) => c.id === diffCheckpointId.value);
    if (!cp) return null;
    const lines = computeLineDiff(cp.bodySnapshot, chapterBodyDraft.value);
    return {
      checkpoint: cp,
      lines,
      changeCount: countDiffChanges(lines),
    };
  });

  function captureBodySelection(textarea) {
    if (!textarea || typeof textarea.selectionStart !== 'number') {
      bodySelection.value = { start: 0, end: 0, text: '' };
      return;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = start !== end ? textarea.value.slice(start, end) : '';
    bodySelection.value = { start, end, text };
  }

  function createCheckpoint(label) {
    const id = `cp-${Date.now()}`;
    checkpoints.value = [
      {
        id,
        label,
        at: new Date().toISOString(),
        chapter: selectedChapter.value,
        bodySnapshot: chapterBodyDraft.value,
      },
      ...checkpoints.value,
    ].slice(0, 6);
    return id;
  }

  function restoreCheckpoint(id) {
    const cp = checkpoints.value.find((c) => c.id === id);
    if (!cp) return;
    chapterBodyDraft.value = cp.bodySnapshot;
    saveMessage.value = `已恢复到 ${cp.label}`;
    diffCheckpointId.value = null;
  }

  function openCheckpointDiff(id) {
    diffCheckpointId.value = id;
  }

  function closeCheckpointDiff() {
    diffCheckpointId.value = null;
  }

  function applyTextToSelection(text) {
    const sel = bodySelection.value;
    const draft = chapterBodyDraft.value;
    if (sel.text && sel.start !== sel.end) {
      chapterBodyDraft.value = draft.slice(0, sel.start) + text + draft.slice(sel.end);
    } else {
      chapterBodyDraft.value = draft ? `${draft}\n\n${text}` : text;
    }
    qualityHints.value = [
      { level: 'ok', text: '已写入编辑器（未保存到磁盘）' },
    ];
  }

  function getControls() {
    return {
      styleStrength: styleStrength.value,
      selectionLocked: selectionLocked.value,
      allowWorldbuildingFill: allowWorldbuildingFill.value,
      goalTag: goalTag.value,
    };
  }

  const agent = useCreatorAgent({
    uiProfile,
    getSelection: () => bodySelection.value,
    getChapterNum: () => selectedChapter.value,
    getBodyDraft: () => chapterBodyDraft.value,
    getControls,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint: (id) => restoreCheckpoint(id),
    onAnnotationFocus: (paragraph) => {
      if (focusParagraphByIndex) focusParagraphByIndex(paragraph, 'inline');
    },
  });

  async function startQuickWrite() {
    if (!intentText.value.trim()) {
      qualityHints.value = [{ level: 'warn', text: '可先输入一句话意图，或直接在正文区开写' }];
      return;
    }
    generateRunning.value = true;
    try {
      await agent.runPlan('quick-write', `一键开写：${intentText.value.trim()}`);
      if (!agent.candidates.value.length && !agent.directorAdvice.value.length) {
        return;
      }
      qualityHints.value = [{ level: 'info', text: '从左侧或下方选择候选，确认后写入正文' }];
    } finally {
      generateRunning.value = false;
    }
  }

  function stopGenerate() {
    generateRunning.value = false;
    agent.generating.value = false;
    agent.statusLine.value = '已停止';
  }

  function dismissQualityHint(index) {
    qualityHints.value = qualityHints.value.filter((_, i) => i !== index);
  }

  function syncQualityFromLogicCheck(result) {
    if (!result) {
      qualityHints.value = [];
      return;
    }
    const hints = [];
    if (result.passed) hints.push({ level: 'ok', text: '逻辑审查通过' });
    else hints.push({ level: 'warn', text: `P0 问题 ${result.p0_count} 条` });
    const issues = (result.issues || []).slice(0, 2);
    for (const issue of issues) {
      hints.push({ level: 'info', text: issue.title || issue.message });
    }
    qualityHints.value = hints.slice(0, 3);
  }

  function toggleSelectionLock() {
    selectionLocked.value = !selectionLocked.value;
    if (selectionLocked.value && hasBodySelection.value) {
      agent.statusLine.value = '选区已锁定，改写不会覆盖选中文字';
    }
  }

  function pulseInlineConflictHighlight() {
    chapterBodyConflictHighlightActive.value = true;
    if (inlineConflictHighlightTimer) clearTimeout(inlineConflictHighlightTimer);
    inlineConflictHighlightTimer = setTimeout(() => {
      chapterBodyConflictHighlightActive.value = false;
      inlineConflictHighlightTimer = null;
    }, 1400);
  }

  function focusInlineConflict(marker) {
    if (!marker) return;
    activeInlineConflictId.value = marker.id;
    if (marker.paragraph && focusParagraphByIndex) {
      focusParagraphByIndex(marker.paragraph, 'inline');
      pulseInlineConflictHighlight();
    }
  }

  function clearInlineConflictFocus() {
    activeInlineConflictId.value = null;
  }

  return {
    workbenchEnabled,
    leftPanelCollapsed,
    intentText,
    intentGenre,
    intentMood,
    bodySelection,
    hasBodySelection,
    checkpoints,
    qualityHints,
    generateIntensity,
    generateRunning,
    styleStrength,
    selectionLocked,
    allowWorldbuildingFill,
    goalTag,
    diffCheckpointId,
    diffView,
    consistencyItems,
    consistencyPanelOpen,
    chapterEntities,
    inlineConflictMarkers,
    activeInlineConflictId,
    chapterBodyConflictHighlightActive,
    showInlineConflictGutter,
    focusInlineConflict,
    clearInlineConflictFocus,
    goalCardLines,
    humanFirstDesk,
    isPanelVisible,
    isLeftRailPanelVisible,
    isPanelCollapsed,
    captureBodySelection,
    createCheckpoint,
    restoreCheckpoint,
    openCheckpointDiff,
    closeCheckpointDiff,
    toggleSelectionLock,
    startQuickWrite,
    stopGenerate,
    dismissQualityHint,
    syncQualityFromLogicCheck,
    agent,
  };
}
