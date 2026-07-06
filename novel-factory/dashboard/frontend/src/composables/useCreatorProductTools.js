/**
 * useCreatorProductTools — 创作偏好、导出、发布向导、介入摘要
 */
import { computed, ref, watch } from 'vue';
import {
  fetchChapters,
  fetchCreatorChapterPreview,
  fetchCreatorPreferences,
  saveCreatorPreferencesApi,
  fetchCreatorMemoryAssets,
  saveCreatorMemoryAnnotation,
  exportCreatorEpub,
  exportCreatorDocx,
  queryCreatorMemory,
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
  fetchCreatorModels,
} from '../api/index.js';
import {
  loadCreatorPreferences,
  saveCreatorPreferences,
  defaultCreatorPreferences,
  CREATOR_MODEL_OPTIONS,
} from '../utils/creatorPreferencesStorage.js';
import { preferencesFromApi, preferencesToApi } from '../utils/creatorPreferencesApi.js';
import {
  buildFullBookMarkdown,
  buildSubmissionPackMarkdown,
  defaultSubmissionChapterNums,
  downloadTextFile,
  downloadBlobFile,
  safeExportFilename,
} from '../utils/creatorExportUtils.js';
import { buildMemoryAssetItems } from '../utils/creatorMemoryAssetsUtils.js';
import { buildStructureGraph } from '../utils/creatorStructureGraphUtils.js';
import { highlightMemorySnippet, formatMemoryCitation } from '../utils/creatorMemoryHighlightUtils.js';
import { buildCreatorPreferencesSummary } from '../utils/creatorPreferencesSummaryUtils.js';
import { useStudioProject } from './useStudioProject.js';

export const CREATOR_PUBLISH_PLATFORMS = [
  { id: 'fanqie', label: '番茄小说' },
  { id: 'qidian', label: '起点中文网' },
  { id: 'jjwxc', label: '晋江文学城' },
  { id: 'custom', label: '自定义平台' },
];

/**
 * @param {{
 *   overview: import('vue').Ref<object|null>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   visibleDeviations: import('vue').ComputedRef<object[]>,
 *   editableVolumes: import('vue').Ref<object[]>,
 *   pillarsText: import('vue').Ref<string>,
 *   globalOutlineText: import('vue').Ref<string>,
 *   logicCheckResult: import('vue').Ref<object|null>,
 *   batchJob: import('vue').Ref<object|null>,
 *   batchRunning: import('vue').Ref<boolean>,
 *   isWorkspaceColumnVisible: (col: string) => boolean,
 *   isDeskDrawerColumn?: (col: string) => boolean,
 *   closeDeskDrawer?: () => void,
 *   setWorkspaceTab: (tab: string) => void,
 *   jumpToChapter: (chapter: number) => Promise<void>,
 *   navigateTo: (page: string, opts?: object) => void,
 *   settingsHasUnsavedChanges?: import('vue').ComputedRef<boolean>,
 * }} deps
 */
export function useCreatorProductTools(deps) {
  const {
    overview,
    error,
    saveMessage,
    visibleDeviations,
    editableVolumes,
    pillarsText,
    globalOutlineText,
    logicCheckResult,
    batchJob,
    batchRunning,
    isWorkspaceColumnVisible,
    isDeskDrawerColumn = () => false,
    closeDeskDrawer = () => {},
    setWorkspaceTab,
    jumpToChapter,
    navigateTo,
    settingsHasUnsavedChanges,
  } = deps;

  const { activeSlug: activeSlugRef } = useStudioProject();
  const activeSlug = activeSlugRef ?? ref(null);

  const preferences = ref(loadCreatorPreferences());
  const preferencesDirty = ref(false);
  const preferencesSavedHint = ref('');
  const preferencesSyncSource = ref('local');
  const creatorModelOptions = ref([...CREATOR_MODEL_OPTIONS]);

  const memoryAssetsPayload = ref(null);
  const memoryAssetsLoading = ref(false);
  const memoryAssetsLoadedOnce = ref(false);
  const memoryFilter = ref('all');

  const exportModalOpen = ref(false);
  const exportMode = ref('full');
  const exportRangeStart = ref(1);
  const exportRangeEnd = ref(10);
  const exportIntro = ref('');
  const exportAuthor = ref('');
  const exportDescription = ref('');
  const exportSubmissionSampleCount = ref(3);
  const exportBusy = ref(false);
  const exportPreview = ref('');

  const memorySearchQuery = ref('');
  const memorySearchScope = ref('all');
  const memorySearchResults = ref([]);
  const memorySearchBusy = ref(false);
  const memorySearchRan = ref(false);
  const memorySearchUsedFallback = ref(false);

  const publishModalOpen = ref(false);
  const publishStep = ref(0);
  const publishPlatform = ref('fanqie');
  const publishIncludeOutline = ref(true);
  const publishIntro = ref('');
  const publishStatus = ref('idle');
  const publishMessage = ref('');
  const publishHistory = ref([]);
  const publishPlatforms = ref([...CREATOR_PUBLISH_PLATFORMS]);
  const publishHistoryModalOpen = ref(false);
  const publishPackPreview = ref('');
  const publishPackBusy = ref(false);
  const publishSubmissionChapters = ref([]);

  const memoryAnnotationSaving = ref(null);

  const structureGraphView = ref('tree');

  watch(
    () => overview.value?.max_chapter,
    (max) => {
      if (max) exportRangeEnd.value = max;
    },
    { immediate: true },
  );

  watch(
    () => [activeSlug.value, overview.value?.pillars_excerpt],
    () => {
      if (!exportAuthor.value) {
        exportAuthor.value = activeSlug.value || '';
      }
      if (!exportDescription.value && overview.value?.pillars_excerpt) {
        exportDescription.value = overview.value.pillars_excerpt.slice(0, 280);
      }
    },
    { immediate: true },
  );

  const memoryAssets = computed(() => {
    if (memoryAssetsPayload.value?.items?.length) {
      return memoryAssetsPayload.value.items;
    }
    return buildMemoryAssetItems({
      overview: overview.value,
      pillarsText: pillarsText.value,
      outlineText: globalOutlineText.value,
    });
  });

  const memoryAssetsFiltered = computed(() => {
    const filter = memoryFilter.value;
    if (filter === 'all') return memoryAssets.value;
    return memoryAssets.value.filter((item) => item.kind === filter);
  });

  const memoryAvailable = computed(() => Boolean(memoryAssetsPayload.value?.memory_available));
  const memoryRagEnabled = computed(
    () => memoryAssetsPayload.value?.memory_rag_enabled ?? preferences.value.memoryRagEnabled,
  );

  const preferencesSummary = computed(() => buildCreatorPreferencesSummary(
    preferences.value,
    {
      memoryRagEnabled: memoryRagEnabled.value,
      modelOptions: creatorModelOptions.value,
    },
  ));

  /** @param {string} ruleId */
  function interventionRuleEnabled(ruleId) {
    return preferences.value.interventionRules?.[ruleId] !== false;
  }

  const structureGraph = computed(() => buildStructureGraph({
    overview: overview.value,
    volumes: editableVolumes.value,
    deviations: visibleDeviations.value,
  }));

  const interventionItems = computed(() => {
    const items = [];
    const alerts = visibleDeviations.value.filter((d) => d.severity === 'alert');
    if (interventionRuleEnabled('deviationAlerts') && alerts.length) {
      items.push({
        id: 'deviation-alerts',
        kind: 'deviation',
        title: `${alerts.length} 处需关注偏离`,
        detail: alerts[0].message || '点击查看脉络详情',
        action: 'pulse',
        chapter: alerts[0].chapter,
      });
    }
    if (interventionRuleEnabled('batchProgress') && (batchRunning.value || batchJob.value?.status === 'running')) {
      items.push({
        id: 'batch-running',
        kind: 'batch',
        title: '批量推进进行中',
        detail: batchJob.value?.message || '可在脉络栏查看进度',
        action: 'pulse',
      });
    }
    const issues = logicCheckResult.value?.issues || [];
    const p0 = issues.filter((i) => i.severity === 'P0' || i.priority === 'P0');
    if (interventionRuleEnabled('logicP0') && p0.length) {
      items.push({
        id: 'logic-p0',
        kind: 'logic',
        title: `${p0.length} 条 P0 逻辑问题`,
        detail: p0[0].message || '请在写栏处理',
        action: 'write',
        chapter: logicCheckResult.value?.chapter,
      });
    }
    if (interventionRuleEnabled('settingsUnsaved') && settingsHasUnsavedChanges?.value) {
      items.push({
        id: 'settings-unsaved',
        kind: 'settings',
        title: '设定尚未保存',
        detail: '支柱或全局大纲有未保存的修改',
        action: 'settings',
      });
    }
    if (interventionRuleEnabled('preferencesUnsaved') && preferencesDirty.value) {
      items.push({
        id: 'preferences-unsaved',
        kind: 'preferences',
        title: '创作偏好尚未保存',
        detail: '模型或记忆检索设置已改但未同步',
        action: 'settings',
      });
    }
    if (
      interventionRuleEnabled('memoryOffline')
      && memoryAssetsLoadedOnce.value
      && !memoryAssetsLoading.value
      && memoryRagEnabled.value
      && !memoryAvailable.value
    ) {
      items.push({
        id: 'memory-offline',
        kind: 'memory',
        title: '记忆系统离线',
        detail: 'RAG 已开启但记忆网关不可用，搜索将降级为本地匹配',
        action: 'memory',
      });
    }
    if (
      interventionRuleEnabled('emptyWriteHint')
      && !items.length
      && overview.value?.chapters_written === 0
      && overview.value?.creation_mode !== 'companion'
      && overview.value?.creation_mode !== 'advance'
    ) {
      items.push({
        id: 'onboarding-write',
        kind: 'hint',
        title: '尚未开始写作',
        detail: '从写栏选择章节或运行入门向导',
        action: 'write',
      });
    }
    return items;
  });

  async function loadCreatorModels() {
    try {
      const data = await fetchCreatorModels();
      if (data.models?.length) {
        creatorModelOptions.value = data.models;
      }
    } catch {
      creatorModelOptions.value = [...CREATOR_MODEL_OPTIONS];
    }
  }

  async function loadPreferencesFromServer() {
    try {
      const data = await fetchCreatorPreferences();
      preferences.value = preferencesFromApi(data);
      saveCreatorPreferences(preferences.value);
      preferencesSyncSource.value = 'server';
      preferencesDirty.value = false;
    } catch {
      preferences.value = loadCreatorPreferences();
      preferencesSyncSource.value = 'local';
    }
  }

  async function loadMemoryAssets() {
    memoryAssetsLoading.value = true;
    try {
      memoryAssetsPayload.value = await fetchCreatorMemoryAssets();
    } catch {
      memoryAssetsPayload.value = null;
    } finally {
      memoryAssetsLoading.value = false;
      memoryAssetsLoadedOnce.value = true;
    }
  }

  async function runMemorySearch() {
    const q = memorySearchQuery.value.trim();
    if (!q) return;
    memorySearchBusy.value = true;
    memorySearchRan.value = false;
    try {
      const data = await queryCreatorMemory({
        query: q,
        scope: memorySearchScope.value,
        top_k: preferences.value.memoryRagTopK,
      });
      memorySearchResults.value = data.results || [];
      memorySearchUsedFallback.value = Boolean(data.used_fallback);
      memorySearchRan.value = true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      memorySearchResults.value = [];
      memorySearchRan.value = true;
    } finally {
      memorySearchBusy.value = false;
    }
  }

  async function loadPublishHistory(limit = 30) {
    try {
      const data = await fetchCreatorPublishHistory(limit);
      publishHistory.value = data.entries || [];
    } catch {
      publishHistory.value = [];
    }
  }

  function openPublishHistoryModal() {
    publishHistoryModalOpen.value = true;
    loadPublishHistory(30);
  }

  function closePublishHistoryModal() {
    publishHistoryModalOpen.value = false;
  }

  async function prefillPublishFromSubmission() {
    exportMode.value = 'submission';
    if (!publishIntro.value.trim()) {
      publishIntro.value = exportIntro.value || exportDescription.value || '';
    }
    publishPackBusy.value = true;
    publishPackPreview.value = '';
    try {
      const chapterNums = await resolveExportChapterNums();
      publishSubmissionChapters.value = chapterNums;
      publishPackPreview.value = await buildExportMarkdown();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      publishSubmissionChapters.value = [];
    } finally {
      publishPackBusy.value = false;
    }
  }

  async function saveMemoryAnnotation(assetId, patch) {
    memoryAnnotationSaving.value = assetId;
    try {
      await saveCreatorMemoryAnnotation(assetId, patch);
      await loadMemoryAssets();
      saveMessage.value = '记忆备注已保存';
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      memoryAnnotationSaving.value = null;
    }
  }

  async function toggleMemoryPin(item) {
    if (!item?.id || item.placeholder) return;
    await saveMemoryAnnotation(item.id, { pinned: !item.pinned });
  }

  async function saveMemoryNote(item, note) {
    if (!item?.id || item.placeholder) return;
    await saveMemoryAnnotation(item.id, { note });
  }

  async function loadPublishPlatforms() {
    try {
      const data = await fetchCreatorPublishPlatforms();
      if (data.platforms?.length) {
        publishPlatforms.value = data.platforms;
      }
    } catch {
      publishPlatforms.value = [...CREATOR_PUBLISH_PLATFORMS];
    }
  }

  const activePublishPlatform = computed(
    () => publishPlatforms.value.find((p) => p.id === publishPlatform.value)
      || publishPlatforms.value[0],
  );

  function exportRequestBody() {
    const body = {
      mode: exportMode.value,
      title: activeSlug.value || '灵文作品',
      author: exportAuthor.value || undefined,
      description: exportDescription.value || undefined,
    };
    if (exportMode.value === 'range') {
      body.start_chapter = Math.min(exportRangeStart.value, exportRangeEnd.value);
      body.end_chapter = Math.max(exportRangeStart.value, exportRangeEnd.value);
    }
    if (exportMode.value === 'submission') {
      body.submission_sample_count = exportSubmissionSampleCount.value;
    }
    return body;
  }

  function markPreferencesDirty() {
    preferencesDirty.value = true;
    preferencesSavedHint.value = '';
  }

  function resetPreferences() {
    preferences.value = defaultCreatorPreferences();
    preferencesDirty.value = true;
    preferencesSavedHint.value = '';
  }

  async function savePreferences() {
    saveCreatorPreferences(preferences.value);
    try {
      await saveCreatorPreferencesApi(preferencesToApi(preferences.value));
      preferencesSyncSource.value = 'server';
      preferencesSavedHint.value = '偏好已同步到项目';
      saveMessage.value = '创作偏好已保存';
    } catch (e) {
      preferencesSyncSource.value = 'local';
      preferencesSavedHint.value = '已保存到本机（服务器暂不可用）';
      saveMessage.value = '创作偏好已保存到本机';
      error.value = e instanceof Error ? e.message : String(e);
    }
    preferencesDirty.value = false;
  }

  function openExportModal(mode = 'full') {
    exportMode.value = mode;
    exportModalOpen.value = true;
    exportPreview.value = '';
    if (overview.value?.max_chapter) {
      exportRangeEnd.value = overview.value.max_chapter;
    }
  }

  function closeExportModal() {
    exportModalOpen.value = false;
    exportBusy.value = false;
  }

  async function loadChapterBodies(chapterNums) {
    const chapters = [];
    for (const num of chapterNums) {
      try {
        const preview = await fetchCreatorChapterPreview(num, { full: true });
        chapters.push({
          chapter: num,
          title: preview.title || `第${num}章`,
          body: preview.body_text || preview.body_preview || preview.excerpt || '',
          excerpt: preview.excerpt,
        });
      } catch {
        const row = overview.value?.chapters?.find((c) => c.chapter === num);
        chapters.push({
          chapter: num,
          title: `第${num}章`,
          body: row?.excerpt || '',
          excerpt: row?.excerpt,
        });
      }
    }
    return chapters;
  }

  async function resolveExportChapterNums() {
    if (exportMode.value === 'range') {
      const start = Math.min(exportRangeStart.value, exportRangeEnd.value);
      const end = Math.max(exportRangeStart.value, exportRangeEnd.value);
      const nums = [];
      for (let n = start; n <= end; n += 1) nums.push(n);
      return nums;
    }
    if (exportMode.value === 'submission') {
      const resp = await fetchChapters();
      const nums = (resp.chapters || [])
        .filter((c) => c.has_body)
        .map((c) => c.chapter);
      return defaultSubmissionChapterNums(
        nums,
        overview.value?.max_chapter,
        exportSubmissionSampleCount.value,
      );
    }
    const resp = await fetchChapters();
    return (resp.chapters || [])
      .filter((c) => c.has_body)
      .map((c) => c.chapter)
      .sort((a, b) => a - b);
  }

  async function buildExportMarkdown() {
    const chapterNums = await resolveExportChapterNums();
    const chapters = await loadChapterBodies(chapterNums);
    const projectTitle = activeSlug.value || '灵文作品';
    const pillars = pillarsText.value || overview.value?.pillars_excerpt || '';
    const outline = globalOutlineText.value || overview.value?.global_outline_excerpt || '';

    if (exportMode.value === 'submission') {
      return buildSubmissionPackMarkdown({
        projectTitle,
        intro: exportIntro.value,
        pillars,
        outline,
        sampleChapters: chapters,
      });
    }
    return buildFullBookMarkdown({ projectTitle, pillars, outline, chapters });
  }

  async function refreshExportPreview() {
    exportBusy.value = true;
    try {
      exportPreview.value = await buildExportMarkdown();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  async function runExportDownload() {
    exportBusy.value = true;
    try {
      const markdown = await buildExportMarkdown();
      const slug = activeSlug.value || 'novel';
      const suffix = exportMode.value === 'submission' ? 'submission' : exportMode.value;
      downloadTextFile(safeExportFilename(slug, suffix), markdown);
      saveMessage.value = '作品已导出为 Markdown';
      closeExportModal();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  async function runExportEpub() {
    exportBusy.value = true;
    try {
      const slug = activeSlug.value || 'novel';
      const blob = await exportCreatorEpub(exportRequestBody());
      downloadBlobFile(safeExportFilename(slug, exportMode.value).replace(/\.md$/, '.epub'), blob);
      saveMessage.value = '作品已导出为 EPUB';
      closeExportModal();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  async function runExportDocx() {
    exportBusy.value = true;
    try {
      const slug = activeSlug.value || 'novel';
      const blob = await exportCreatorDocx(exportRequestBody());
      downloadBlobFile(safeExportFilename(slug, exportMode.value).replace(/\.md$/, '.docx'), blob);
      saveMessage.value = '作品已导出为 DOCX';
      closeExportModal();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  async function openPublishWizard() {
    publishModalOpen.value = true;
    publishStep.value = 0;
    publishStatus.value = 'idle';
    publishMessage.value = '';
    await Promise.all([loadPublishHistory(), loadPublishPlatforms()]);
  }

  function closePublishWizard() {
    publishModalOpen.value = false;
    publishStatus.value = 'idle';
  }

  function nextPublishStep() {
    const next = Math.min(publishStep.value + 1, 3);
    if (publishStep.value === 0 && next === 1) {
      prefillPublishFromSubmission();
    }
    publishStep.value = next;
  }

  function prevPublishStep() {
    publishStep.value = Math.max(publishStep.value - 1, 0);
  }

  async function submitPublish() {
    publishStatus.value = 'submitting';
    publishMessage.value = '';
    try {
      const entry = await submitCreatorPublish({
        platform: publishPlatform.value,
        include_outline: publishIncludeOutline.value,
        intro: publishIntro.value || exportIntro.value,
        mode: 'submission',
      });
      publishStatus.value = 'success';
      publishMessage.value = entry.message || `已提交至 ${publishPlatform.value}（${entry.status}）`;
      saveMessage.value = publishMessage.value;
      await loadPublishHistory();
    } catch (e) {
      publishStatus.value = 'idle';
      error.value = e instanceof Error ? e.message : String(e);
    }
  }

  async function handleInterventionAction(item) {
    if (!item) return;
    if (item.action === 'pulse') {
      setWorkspaceTab('pulse');
      if (item.chapter) await jumpToChapter(item.chapter);
      return;
    }
    if (item.action === 'write') {
      setWorkspaceTab('write');
      if (item.chapter) await jumpToChapter(item.chapter);
      return;
    }
    if (item.action === 'memory') {
      setWorkspaceTab('memory');
      return;
    }
    if (item.action === 'settings') {
      setWorkspaceTab('settings');
      return;
    }
    if (item.action === 'decisions') {
      navigateTo('decisions', { clearFocus: true });
    }
  }

  function goToSettingsForAsset(item) {
    if (item?.editable) {
      setWorkspaceTab('settings');
    }
  }

  const panelContext = {
    preferences,
    preferencesDirty,
    preferencesSummary,
    creatorModelOptions,
    loadCreatorModels,
    preferencesSavedHint,
    preferencesSyncSource,
    markPreferencesDirty,
    resetPreferences,
    savePreferences,
    loadPreferencesFromServer,
    memoryAssets,
    memoryAssetsFiltered,
    memoryAssetsLoading,
    memoryFilter,
    memoryAvailable,
    memoryRagEnabled,
    loadMemoryAssets,
    saveMemoryAnnotation,
    toggleMemoryPin,
    saveMemoryNote,
    memoryAnnotationSaving,
    runMemorySearch,
    structureGraph,
    structureGraphView,
    isWorkspaceColumnVisible,
    deskDrawerActive: () => isDeskDrawerColumn('memory'),
    closeDeskDrawer,
    memorySearchQuery,
    memorySearchScope,
    memorySearchResults,
    memorySearchBusy,
    memorySearchRan,
    memorySearchUsedFallback,
    highlightMemorySnippet,
    formatMemoryCitation,
    exportModalOpen,
    exportMode,
    exportRangeStart,
    exportRangeEnd,
    exportIntro,
    exportAuthor,
    exportDescription,
    exportSubmissionSampleCount,
    exportBusy,
    exportPreview,
    openExportModal,
    closeExportModal,
    refreshExportPreview,
    runExportDownload,
    runExportEpub,
    runExportDocx,
    publishModalOpen,
    publishStep,
    publishPlatform,
    publishIncludeOutline,
    publishIntro,
    publishStatus,
    publishMessage,
    publishHistory,
    publishPlatforms,
    publishHistoryModalOpen,
    publishPackPreview,
    publishPackBusy,
    publishSubmissionChapters,
    activePublishPlatform,
    openPublishWizard,
    closePublishWizard,
    openPublishHistoryModal,
    closePublishHistoryModal,
    prefillPublishFromSubmission,
    nextPublishStep,
    prevPublishStep,
    submitPublish,
    loadPublishHistory,
    loadPublishPlatforms,
    interventionItems,
    handleInterventionAction,
    goToSettingsForAsset,
    jumpToChapter,
    setWorkspaceTab,
  };

  return {
    panelContext,
    loadPreferencesFromServer,
    loadMemoryAssets,
    loadCreatorModels,
  };
}
