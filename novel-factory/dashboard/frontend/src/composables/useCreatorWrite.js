/**
 * useCreatorWrite — 写栏章节预览与内嵌编辑（从 CreatorPage 抽出）
 */
import { computed, nextTick, onUnmounted, ref, watch } from 'vue';
import {
  fetchCreatorChapterPreview,
  saveCreatorChapterBody,
  saveCreatorChapterOutline,
  runCreatorLogicCheck,
} from '../api/index.js';
import { useCreatorWriteWorkbench } from './useCreatorWriteWorkbench.js';
import { extractMentionedEntityNames } from '../utils/creatorChapterEntityUtils.js';
import { saveWriteResume } from '../utils/writeResumeStorage.js';

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
 * } deps
 */
export function useCreatorWrite(deps) {
  const {
    uiProfile, overview, error, saveMessage, handleSaveError, onAfterChapterSave,
    isWorkspaceColumnVisible, workspaceTabsEnabled, visibleDeviations,
    deviationHighlightEnabled, highlightedDeviationChapter,
    logicCheckRunning, logicCheckResult, runCompanionLogicCheck,
    openVolumeSummaryForRange,
  } = deps;

const selectedChapter = ref(null);
const chapterPreview = ref(null);
const chapterBodyDraft = ref('');
const chapterOutlineDraft = ref('');
const chapterBodySaving = ref(false);
const chapterOutlineSaving = ref(false);
const chapterBodyTextareaRef = ref(null);
const bodyLastSavedAt = ref(null);
const bodyAutoSaveStatus = ref('idle');
let lastPersistedBody = '';
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

const deviationChapters = computed(() => {
  const set = new Set();
  for (const d of overview.value?.deviations || []) {
    if (d.chapter) set.add(d.chapter);
  }
  return set;
});

const alertChapters = computed(() => {
  const set = new Set();
  for (const d of overview.value?.deviations || []) {
    if (d.severity === 'alert' && d.chapter) set.add(d.chapter);
  }
  return set;
});

const visibleChapters = computed(() =>
  (overview.value?.chapters || []).filter((ch) => ch.chapter <= 15),
);

const showCompanionLogicCheckInWrite = computed(
  () => uiProfile.value.primary_action === 'logic_check' && workspaceTabsEnabled.value,
);

let memoryAssetsCache = [];

function syncMemoryAssets(items) {
  memoryAssetsCache = Array.isArray(items) ? items : [];
}

const wb = useCreatorWriteWorkbench({
  uiProfile,
  overview,
  chapterBodyDraft,
  selectedChapter,
  saveMessage,
  logicCheckResult,
  visibleDeviations,
  getMemoryAssets: () => memoryAssetsCache,
  focusParagraphByIndex: (paragraph, source = 'inline') => {
    focusIssueParagraph({ paragraph }, null, source);
  },
});

watch(logicCheckResult, (result) => {
  wb.syncQualityFromLogicCheck(result);
});

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
  if (draft === lastPersistedBody) {
    bodyAutoSaveStatus.value = bodyLastSavedAt.value ? 'saved' : 'idle';
    return;
  }
  bodyAutoSaveStatus.value = 'pending';
  if (autoSaveTimer) clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(() => {
    autoSaveChapterBody();
  }, 2000);
});

async function autoSaveChapterBody() {
  if (!selectedChapter.value || chapterBodySaving.value) return;
  if (chapterBodyDraft.value === lastPersistedBody) return;
  chapterBodySaving.value = true;
  bodyAutoSaveStatus.value = 'saving';
  try {
    chapterPreview.value = await saveCreatorChapterBody(selectedChapter.value, chapterBodyDraft.value);
    lastPersistedBody = chapterBodyDraft.value;
    bodyLastSavedAt.value = new Date();
    bodyAutoSaveStatus.value = 'saved';
    const slug = overview.value?.slug;
    if (slug) {
      saveWriteResume(slug, {
        chapter: selectedChapter.value,
        projectName: overview.value?.name,
      });
    }
    await onAfterChapterSave();
  } catch {
    bodyAutoSaveStatus.value = 'error';
  } finally {
    chapterBodySaving.value = false;
  }
}

function bindChapterBodyTextareaRef(el) {
  chapterBodyTextareaRef.value = el;
}

function maybeAutoSelectWritingChapter() {
  if (!workspaceTabsEnabled.value || selectedChapter.value) return;
  const ov = overview.value;
  if (!ov || (ov.creation_mode !== 'companion' && ov.creation_mode !== 'advance')) return;
  const chapters = ov.chapters || [];
  const target = chapters.find((ch) => !ch.has_body) || chapters[0];
  if (target?.chapter) {
    selectChapter(target.chapter);
  }
}

function chapterRowClass(chapter) {
  if (alertChapters.value.has(chapter)) return 'chapter-row--alert';
  if (deviationChapters.value.has(chapter)) return 'chapter-row--warn';
  const ch = overview.value?.chapters?.find((c) => c.chapter === chapter);
  if (ch?.has_body) return 'chapter-row--done';
  return '';
}

function chapterVolumeLabel(chapter) {
  const hit = visibleDeviations.value.find((d) => d.chapter === chapter);
  return hit?.volume_label || '';
}

function chapterRowTitle(chapter) {
  const hit = visibleDeviations.value.find((d) => d.chapter === chapter);
  if (hit?.message) return hit.message;
  const ch = overview.value?.chapters?.find((c) => c.chapter === chapter);
  if (ch?.has_body) return `已写 ${ch.word_count || 0} 字`;
  if (ch?.has_outline) return '仅有大纲';
  return '尚未开始';
}

async function selectChapter(chapter) {
  selectedChapter.value = chapter;
  previewLoading.value = true;
  chapterPreview.value = null;
  chapterBodyDraft.value = '';
  chapterOutlineDraft.value = '';
  if (chapterRecheckResult.value?.chapter !== chapter) {
    chapterRecheckResult.value = null;
  }
  try {
    const full = Boolean(
      uiProfile.value.chapter_inline_edit
        || uiProfile.value.chapter_full_preview
        || uiProfile.value.chapter_outline_inline_edit
        || uiProfile.value.chapter_outline_read_preview,
    );
    chapterPreview.value = await fetchCreatorChapterPreview(chapter, { full });
    chapterBodyDraft.value = chapterPreview.value.body_text ?? chapterPreview.value.body_preview ?? '';
    chapterOutlineDraft.value = chapterPreview.value.outline_text ?? chapterPreview.value.outline_preview ?? '';
    lastPersistedBody = chapterBodyDraft.value;
    bodyLastSavedAt.value = null;
    bodyAutoSaveStatus.value = 'idle';
    const slug = overview.value?.slug;
    if (slug) {
      saveWriteResume(slug, { chapter, projectName: overview.value?.name });
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    previewLoading.value = false;
  }
}

async function jumpToChapter(chapter) {
  if (!chapter) return;
  await selectChapter(chapter);
  await nextTick();
  try {
    document.querySelector('[data-testid="chapter-preview-panel"]')?.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  } catch {
    /* jsdom */
  }
}

async function recheckChapterP0(chapter) {
  logicCheckRunning.value = true;
  try {
    const result = await runCreatorLogicCheck({ chapter });
    if (uiProfile.value.chapter_recheck_inline) {
      chapterRecheckResult.value = { ...result, chapter };
    } else {
      logicCheckResult.value = result;
    }
    if (result.p0_count > 0) {
      saveMessage.value = `ch${String(chapter).padStart(3, '0')} 保存后复查：发现 ${result.p0_count} 条 P0`;
    }
  } catch (e) {
    handleSaveError(e);
  } finally {
    logicCheckRunning.value = false;
  }
}

async function saveChapterBody() {
  if (!selectedChapter.value) return;
  chapterBodySaving.value = true;
  saveMessage.value = '';
  try {
    chapterPreview.value = await saveCreatorChapterBody(selectedChapter.value, chapterBodyDraft.value);
    chapterBodyDraft.value = chapterPreview.value.body_text ?? chapterBodyDraft.value;
    chapterOutlineDraft.value = chapterPreview.value.outline_text ?? chapterOutlineDraft.value;
    lastPersistedBody = chapterBodyDraft.value;
    bodyLastSavedAt.value = new Date();
    bodyAutoSaveStatus.value = 'saved';
    const mentioned = extractMentionedEntityNames(chapterBodyDraft.value, memoryAssetsCache);
    saveMessage.value = mentioned.length
      ? `ch${String(selectedChapter.value).padStart(3, '0')} 正文已保存 · 涉及：${mentioned.join('、')}`
      : `ch${String(selectedChapter.value).padStart(3, '0')} 正文已保存`;
    const slug = overview.value?.slug;
    if (slug) {
      saveWriteResume(slug, {
        chapter: selectedChapter.value,
        projectName: overview.value?.name,
      });
    }
    await onAfterChapterSave();
    if (uiProfile.value.chapter_save_p0_recheck) {
      await recheckChapterP0(selectedChapter.value);
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    chapterBodySaving.value = false;
  }
}

async function saveChapterOutline() {
  if (!selectedChapter.value) return;
  chapterOutlineSaving.value = true;
  saveMessage.value = '';
  try {
    chapterPreview.value = await saveCreatorChapterOutline(selectedChapter.value, chapterOutlineDraft.value);
    chapterOutlineDraft.value = chapterPreview.value.outline_text ?? chapterOutlineDraft.value;
    chapterBodyDraft.value = chapterPreview.value.body_text ?? chapterBodyDraft.value;
    saveMessage.value = `ch${String(selectedChapter.value).padStart(3, '0')} 大纲已保存`;
    await onAfterChapterSave();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    chapterOutlineSaving.value = false;
  }
}

function pulseChapterBodyHighlight(issueIdx, source = 'recheck') {
  const bodyHighlight = uiProfile.value.recheck_issue_highlight
    || (uiProfile.value.issue_paragraph_highlight_unified && (source === 'logic' || source === 'inline'))
    || source === 'inline';
  if (bodyHighlight) {
    if (source === 'recheck') {
      activeRecheckIssueIdx.value = issueIdx ?? null;
    }
    chapterBodyHighlightActive.value = true;
    if (chapterBodyHighlightTimer) {
      clearTimeout(chapterBodyHighlightTimer);
    }
    chapterBodyHighlightTimer = setTimeout(() => {
      chapterBodyHighlightActive.value = false;
      if (source === 'recheck') {
        activeRecheckIssueIdx.value = null;
      }
      chapterBodyHighlightTimer = null;
    }, 1200);
  } else if (source === 'recheck') {
    activeRecheckIssueIdx.value = issueIdx ?? null;
    if (chapterBodyHighlightTimer) {
      clearTimeout(chapterBodyHighlightTimer);
    }
    chapterBodyHighlightTimer = setTimeout(() => {
      activeRecheckIssueIdx.value = null;
      chapterBodyHighlightTimer = null;
    }, 1200);
  }
}

function focusIssueParagraph(issue, issueIdx, source = 'recheck') {
  if (!uiProfile.value.recheck_issue_paragraph_jump || !issue?.paragraph) return;
  const textarea = chapterBodyTextareaRef.value;
  if (!textarea) return;
  const paragraphs = chapterBodyDraft.value.split(/\n\s*\n/);
  const idx = Math.max(0, Number(issue.paragraph) - 1);
  const target = paragraphs[idx] ?? '';
  if (!target) return;
  const offset = chapterBodyDraft.value.indexOf(target);
  if (offset < 0) return;
  textarea.focus();
  textarea.setSelectionRange(offset, offset + target.length);
  try {
    const lineHeight = 16;
    textarea.scrollTop = Math.max(0, (offset / Math.max(chapterBodyDraft.value.length, 1)) * textarea.scrollHeight - lineHeight * 2);
  } catch {
    /* jsdom */
  }
  pulseChapterBodyHighlight(issueIdx, source);
}

function pulseLogicCheckIssueHighlight(issueIdx) {
  if (!uiProfile.value.logic_check_issue_highlight && !uiProfile.value.issue_paragraph_highlight_unified) {
    return;
  }
  activeLogicCheckIssueIdx.value = issueIdx ?? null;
  if (logicCheckIssueHighlightTimer) {
    clearTimeout(logicCheckIssueHighlightTimer);
  }
  logicCheckIssueHighlightTimer = setTimeout(() => {
    activeLogicCheckIssueIdx.value = null;
    logicCheckIssueHighlightTimer = null;
  }, 1200);
}

function pulseDeviationHighlight(chapter) {
  if (!deviationHighlightEnabled.value || !chapter) return;
  highlightedDeviationChapter.value = chapter;
  if (deviationHighlightTimer) {
    clearTimeout(deviationHighlightTimer);
  }
  deviationHighlightTimer = setTimeout(() => {
    highlightedDeviationChapter.value = null;
    deviationHighlightTimer = null;
  }, 1200);
}

async function handleLogicCheckIssueClick(issue, issueIdx) {
  if (!issue?.chapter) return;
  pulseLogicCheckIssueHighlight(issueIdx);
  await jumpToChapter(issue.chapter);
  if (uiProfile.value.recheck_issue_paragraph_jump && issue.paragraph) {
    await nextTick();
    focusIssueParagraph(issue, issueIdx, 'logic');
  }
}

async function handleDeviationClick(deviation) {
  if (!deviation?.chapter || !uiProfile.value.deviation_chapter_jump) return;
  pulseDeviationHighlight(deviation.chapter);
  await jumpToChapter(deviation.chapter);
}

function batchDeviationsInRange(start, end) {
  return visibleDeviations.value
    .filter((row) => row.chapter && row.chapter >= start && row.chapter <= end)
    .sort((a, b) => a.chapter - b.chapter);
}

async function scrollToBatchDeviationList(start, end) {
  if (!uiProfile.value.batch_scroll_deviation_list) return;
  const rows = batchDeviationsInRange(start, end);
  if (!rows.length) return;
  pulseDeviationHighlight(rows[0].chapter);
  await nextTick();
  try {
    document.querySelector('[data-testid="deviation-list"]')?.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  } catch {
    /* jsdom */
  }
}

async function openFirstBatchDeviationChapter(start, end) {
  if (!uiProfile.value.batch_open_first_deviation) return;
  const rows = batchDeviationsInRange(start, end);
  if (!rows.length) return;
  pulseDeviationHighlight(rows[0].chapter);
  await jumpToChapter(rows[0].chapter);
}

function updateBatchDeviationInlineSummary(start, end) {
  if (!uiProfile.value.batch_deviation_inline_summary) {
    batchDeviationInlineSummary.value = null;
    return;
  }
  const items = batchDeviationsInRange(start, end);
  batchDeviationInlineSummary.value = items.length
    ? { start, end, items }
    : null;
}

async function linkBatchDeviationInlineSummary(start, end) {
  if (
    !batchDeviationInlineSummary.value
    || !uiProfile.value.batch_deviation_summary_link
    || !overview.value?.volume_summaries?.length
  ) {
    return;
  }
  await nextTick();
  openVolumeSummaryForRange(start, end);
}

function dismissBatchDeviationInlineSummary() {
  batchDeviationInlineSummary.value = null;
}

function navigateIssueList(event, issues, currentIdx, onSelect, testIdPrefix) {
  if (!uiProfile.value.issue_keyboard_navigation || !issues?.length) return;
  if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
  event.preventDefault();
  const delta = event.key === 'ArrowDown' ? 1 : -1;
  const nextIdx = Math.max(0, Math.min(issues.length - 1, currentIdx + delta));
  if (nextIdx === currentIdx) return;
  onSelect(issues[nextIdx], nextIdx);
  nextTick(() => {
    try {
      document.querySelector(`[data-testid="${testIdPrefix}-${nextIdx}"]`)?.focus?.();
    } catch {
      /* jsdom */
    }
  });
}

function onRecheckIssueKeydown(event, issue, idx) {
  navigateIssueList(
    event,
    chapterRecheckResult.value?.issues,
    idx,
    (item, newIdx) => focusIssueParagraph(item, newIdx),
    'chapter-recheck-issue',
  );
}

function onLogicCheckIssueKeydown(event, issue, idx) {
  navigateIssueList(
    event,
    logicCheckResult.value?.issues,
    idx,
    (item, newIdx) => handleLogicCheckIssueClick(item, newIdx),
    'logic-check-issue',
  );
}

const panelContext = {
  uiProfile,
  overview,
  isWorkspaceColumnVisible,
  visibleChapters,
  chapterRowClass,
  chapterVolumeLabel,
  chapterRowTitle,
  selectedChapter,
  selectChapter,
  showCompanionLogicCheckInWrite,
  logicCheckRunning,
  runCompanionLogicCheck,
  logicCheckResult,
  activeLogicCheckIssueIdx,
  handleLogicCheckIssueClick,
  onLogicCheckIssueKeydown,
  batchDeviationInlineSummary,
  deviationHighlightEnabled,
  highlightedDeviationChapter,
  handleDeviationClick,
  openVolumeSummaryForRange,
  dismissBatchDeviationInlineSummary,
  chapterPreview,
  previewLoading,
  chapterOutlineDraft,
  chapterOutlineSaving,
  saveChapterOutline,
  chapterBodyDraft,
  chapterBodyHighlightActive,
  bindChapterBodyTextareaRef,
  chapterBodySaving,
  saveChapterBody,
  bodySaveStatusLabel,
  bodyAutoSaveStatus,
  chapterRecheckResult,
  activeRecheckIssueIdx,
  focusIssueParagraph,
  onRecheckIssueKeydown,
  wb,
};

onUnmounted(() => {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = null;
  }
  if (chapterBodyHighlightTimer) {
    clearTimeout(chapterBodyHighlightTimer);
    chapterBodyHighlightTimer = null;
  }
  if (logicCheckIssueHighlightTimer) {
    clearTimeout(logicCheckIssueHighlightTimer);
    logicCheckIssueHighlightTimer = null;
  }
  if (deviationHighlightTimer) {
    clearTimeout(deviationHighlightTimer);
    deviationHighlightTimer = null;
  }
});

return {
  panelContext,
  selectedChapter,
  jumpToChapter,
  handleDeviationClick,
  handleLogicCheckIssueClick,
  scrollToBatchDeviationList,
  openFirstBatchDeviationChapter,
  updateBatchDeviationInlineSummary,
  linkBatchDeviationInlineSummary,
  dismissBatchDeviationInlineSummary,
  maybeAutoSelectWritingChapter,
  onRecheckIssueKeydown,
  onLogicCheckIssueKeydown,
  focusIssueParagraph,
  syncMemoryAssets,
  activeLogicCheckIssueIdx,
};
}
