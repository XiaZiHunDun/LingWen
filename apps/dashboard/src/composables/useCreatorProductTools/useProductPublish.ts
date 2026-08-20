/**
 * useProductPublish — 发布向导、历史、平台管理
 *
 * Phase 19 Task 1：从 useCreatorProductTools.js 拆出。
 * 负责: 发布向导 4 步流程 + 平台列表 + 历史 + 投稿包预填。
 *
 * 依赖 (deps):
 * - exportIntro, exportDescription: 来自 export 子模块的导出字段
 * - buildExportMarkdown: 来自 export 子模块的 markdown 构造
 * - error, saveMessage
 * - setWorkspaceTab
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
} from '../../api/index.js';

export const CREATOR_PUBLISH_PLATFORMS = [
  { id: 'fanqie', label: '番茄小说' },
  { id: 'qidian', label: '起点中文网' },
  { id: 'jjwxc', label: '晋江文学城' },
  { id: 'custom', label: '自定义平台' },
];

export interface PublishDeps {
  exportIntro: Ref<string>;
  exportDescription: Ref<string>;
  buildExportMarkdown: () => Promise<string>;
  resolveExportChapterNums: () => Promise<number[]>;
  setExportMode: (mode: string) => void;
  error: Ref<string | null>;
  saveMessage: Ref<string>;
}

export interface ProductPublishReturn {
  publishModalOpen: Ref<boolean>;
  publishStep: Ref<number>;
  publishPlatform: Ref<string>;
  publishIncludeOutline: Ref<boolean>;
  publishIntro: Ref<string>;
  publishStatus: Ref<string>;
  publishMessage: Ref<string>;
  publishHistory: Ref<Array<Record<string, unknown>>>;
  publishPlatforms: Ref<Array<{ id: string; label: string }>>;
  publishHistoryModalOpen: Ref<boolean>;
  publishPackPreview: Ref<string>;
  publishPackBusy: Ref<boolean>;
  publishSubmissionChapters: Ref<Array<number>>;
  activePublishPlatform: ComputedRef<{ id: string; label: string }>;
  openPublishWizard: () => Promise<void>;
  closePublishWizard: () => void;
  openPublishHistoryModal: () => void;
  closePublishHistoryModal: () => void;
  prefillPublishFromSubmission: () => Promise<void>;
  nextPublishStep: () => void;
  prevPublishStep: () => void;
  submitPublish: () => Promise<void>;
  loadPublishHistory: (limit?: number) => Promise<void>;
  loadPublishPlatforms: () => Promise<void>;
}

export function useProductPublish(deps: PublishDeps): ProductPublishReturn {
  const {
    exportIntro,
    exportDescription,
    buildExportMarkdown,
    resolveExportChapterNums,
    setExportMode,
    error,
    saveMessage,
  } = deps;

  const publishModalOpen = ref(false);
  const publishStep = ref(0);
  const publishPlatform = ref('fanqie');
  const publishIncludeOutline = ref(true);
  const publishIntro = ref('');
  const publishStatus = ref('idle');
  const publishMessage = ref('');
  const publishHistory = ref<Array<Record<string, unknown>>>([]);
  const publishPlatforms = ref<Array<{ id: string; label: string }>>([...CREATOR_PUBLISH_PLATFORMS]);
  const publishHistoryModalOpen = ref(false);
  const publishPackPreview = ref('');
  const publishPackBusy = ref(false);
  const publishSubmissionChapters = ref<Array<number>>([]);

  const activePublishPlatform = computed(() =>
    publishPlatforms.value.find((p) => p.id === publishPlatform.value)
    || publishPlatforms.value[0],
  );

  async function loadPublishHistory(limit: number = 30): Promise<void> {
    try {
      const data = await fetchCreatorPublishHistory(limit) as { entries?: Array<Record<string, unknown>> };
      publishHistory.value = data.entries || [];
    } catch {
      publishHistory.value = [];
    }
  }

  function openPublishHistoryModal(): void {
    publishHistoryModalOpen.value = true;
    void loadPublishHistory(30);
  }

  function closePublishHistoryModal(): void {
    publishHistoryModalOpen.value = false;
  }

  async function prefillPublishFromSubmission(): Promise<void> {
    setExportMode('submission');
    publishPackBusy.value = true;
    publishPackPreview.value = '';
    try {
      const chapterNums = await resolveExportChapterNums();
      publishSubmissionChapters.value = chapterNums;
      if (!publishIntro.value.trim()) {
        publishIntro.value = exportIntro.value || exportDescription.value || '';
      }
      publishPackPreview.value = await buildExportMarkdown();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      publishSubmissionChapters.value = [];
    } finally {
      publishPackBusy.value = false;
    }
  }

  async function loadPublishPlatforms(): Promise<void> {
    try {
      const data = await fetchCreatorPublishPlatforms() as { platforms?: Array<{ id: string; label: string }> };
      if (data.platforms?.length) {
        publishPlatforms.value = data.platforms;
      }
    } catch {
      publishPlatforms.value = [...CREATOR_PUBLISH_PLATFORMS];
    }
  }

  async function openPublishWizard(): Promise<void> {
    publishModalOpen.value = true;
    publishStep.value = 0;
    publishStatus.value = 'idle';
    publishMessage.value = '';
    await Promise.all([loadPublishHistory(), loadPublishPlatforms()]);
  }

  function closePublishWizard(): void {
    publishModalOpen.value = false;
    publishStatus.value = 'idle';
  }

  function nextPublishStep(): void {
    const next = Math.min(publishStep.value + 1, 3);
    if (publishStep.value === 0 && next === 1) {
      void prefillPublishFromSubmission();
    }
    publishStep.value = next;
  }

  function prevPublishStep(): void {
    publishStep.value = Math.max(publishStep.value - 1, 0);
  }

  async function submitPublish(): Promise<void> {
    publishStatus.value = 'submitting';
    publishMessage.value = '';
    try {
      const entry = await submitCreatorPublish({
        platform: publishPlatform.value,
        include_outline: publishIncludeOutline.value,
        intro: publishIntro.value || exportIntro.value,
        mode: 'submission',
      }) as { message?: string; status?: string };
      publishStatus.value = 'success';
      publishMessage.value = entry.message || `已提交至 ${publishPlatform.value}（${entry.status}）`;
      saveMessage.value = publishMessage.value;
      await loadPublishHistory();
    } catch (e) {
      publishStatus.value = 'idle';
      error.value = e instanceof Error ? e.message : String(e);
    }
  }

  return {
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
  };
}
