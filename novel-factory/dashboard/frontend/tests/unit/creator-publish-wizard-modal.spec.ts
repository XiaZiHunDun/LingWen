// tests/unit/creator-publish-wizard-modal.spec.ts — CreatorPublishWizardModal.vue 挂载

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, computed } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorPublishWizardModal from '../../src/components/creator/CreatorPublishWizardModal.vue';
import {
  CREATOR_PRODUCT_TOOLS_KEY,
  createCreatorProductToolsContext,
} from '../../src/components/creator/creatorProductToolsKey.js';
import { useCreatorProductTools } from '../../src/composables/useCreatorProductTools.js';
import { byTestid } from '../helpers/by-testid';

const apiMocks = vi.hoisted(() => ({
  fetchChapters: vi.fn(),
  fetchCreatorChapterPreview: vi.fn(),
  fetchCreatorPreferences: vi.fn(),
  saveCreatorPreferencesApi: vi.fn(),
  fetchCreatorMemoryAssets: vi.fn(),
  saveCreatorMemoryAnnotation: vi.fn(),
  exportCreatorEpub: vi.fn(),
  exportCreatorDocx: vi.fn(),
  queryCreatorMemory: vi.fn(),
  submitCreatorPublish: vi.fn(),
  fetchCreatorPublishHistory: vi.fn(),
  fetchCreatorPublishPlatforms: vi.fn(),
  fetchCreatorModels: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchChapters: apiMocks.fetchChapters,
  fetchCreatorChapterPreview: apiMocks.fetchCreatorChapterPreview,
  fetchCreatorPreferences: apiMocks.fetchCreatorPreferences,
  saveCreatorPreferencesApi: apiMocks.saveCreatorPreferencesApi,
  fetchCreatorMemoryAssets: apiMocks.fetchCreatorMemoryAssets,
  saveCreatorMemoryAnnotation: apiMocks.saveCreatorMemoryAnnotation,
  exportCreatorEpub: apiMocks.exportCreatorEpub,
  exportCreatorDocx: apiMocks.exportCreatorDocx,
  queryCreatorMemory: apiMocks.queryCreatorMemory,
  submitCreatorPublish: apiMocks.submitCreatorPublish,
  fetchCreatorPublishHistory: apiMocks.fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms: apiMocks.fetchCreatorPublishPlatforms,
  fetchCreatorModels: apiMocks.fetchCreatorModels,
}));

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({ activeSlug: ref('demo-novel') }),
}));

function makeProductToolsContext() {
  const overview = ref({
    max_chapter: 5,
    chapters_written: 1,
    chapters: [{ chapter: 1, has_body: true, excerpt: '片段' }],
    pillars_excerpt: '支柱',
    global_outline_excerpt: '大纲',
  });
  const isWorkspaceColumnVisible = (col: string) => col === 'memory' || col === 'settings';
  const { panelContext } = useCreatorProductTools({
    overview,
    error: ref(null),
    saveMessage: ref(''),
    visibleDeviations: computed(() => []),
    editableVolumes: ref([{ label: '一', start_chapter: 1, end_chapter: 5, locked: false }]),
    pillarsText: ref('支柱全文'),
    globalOutlineText: ref('大纲全文'),
    logicCheckResult: ref(null),
    batchJob: ref(null),
    batchRunning: ref(false),
    isWorkspaceColumnVisible,
    setWorkspaceTab: vi.fn(),
    jumpToChapter: vi.fn(),
    navigateTo: vi.fn(),
    settingsHasUnsavedChanges: computed(() => false),
  });
  return createCreatorProductToolsContext(panelContext) as ReturnType<typeof createCreatorProductToolsContext> & {
    openPublishWizard: () => Promise<void>;
    closePublishWizard: () => void;
    nextPublishStep: () => void;
    prevPublishStep: () => void;
    submitPublish: () => Promise<void>;
    openExportModal: (mode: string) => void;
    publishModalOpen: boolean;
    publishStep: number;
    publishStatus: string;
    publishMessage: string;
    publishHistory: Array<Record<string, unknown>>;
  };
}

function mountPublishModal(pt = makeProductToolsContext()) {
  const wrapper = mount(CreatorPublishWizardModal, {
    global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
  });
  return { wrapper, pt };
}

describe('CreatorPublishWizardModal component', () => {
  beforeEach(() => {
    apiMocks.fetchChapters.mockResolvedValue({ chapters: [{ chapter: 1, has_body: true }] });
    apiMocks.fetchCreatorChapterPreview.mockResolvedValue({ title: '第一章', body_text: '正文' });
    apiMocks.fetchCreatorPublishHistory.mockResolvedValue({ slug: 'demo-novel', entries: [] });
    apiMocks.fetchCreatorPublishPlatforms.mockResolvedValue({
      slug: 'demo-novel',
      platforms: [
        {
          id: 'fanqie',
          label: '番茄小说',
          connection: 'stub',
          capabilities: { oauth_required: true, max_intro_chars: 500, supports_submission_pack: true },
        },
        {
          id: 'qidian',
          label: '起点中文网',
          connection: 'disconnected',
          capabilities: { oauth_required: true, max_intro_chars: 2000 },
        },
      ],
    });
    apiMocks.submitCreatorPublish.mockResolvedValue({ message: '已提交发布队列', status: 'queued' });
  });

  it('renders nothing when publish modal is closed', () => {
    const { wrapper } = mountPublishModal();
    expect(wrapper.find(byTestid('creator-publish-modal')).exists()).toBe(false);
  });

  it('shows platform step with connection tags', async () => {
    const pt = makeProductToolsContext();
    await pt.openPublishWizard();
    const { wrapper } = mountPublishModal(pt);
    expect(wrapper.find(byTestid('publish-step-platform')).exists()).toBe(true);
    expect(wrapper.find(byTestid('publish-platform-fanqie')).text()).toContain('番茄小说');
    expect(wrapper.find(byTestid('publish-platform-fanqie')).text()).toContain('占位适配');
    expect(wrapper.find(byTestid('publish-platform-qidian')).text()).toContain('未连接');
  });

  it('advances through format and confirm steps', async () => {
    const pt = makeProductToolsContext();
    await pt.openPublishWizard();
    const { wrapper } = mountPublishModal(pt);

    await wrapper.find(byTestid('publish-next-btn')).trigger('click');
    await flushPromises();
    expect(wrapper.find(byTestid('publish-step-format')).exists()).toBe(true);
    expect(wrapper.find(byTestid('publish-platform-caps')).text()).toContain('500');

    await wrapper.find(byTestid('publish-intro')).setValue('试读简介');
    await wrapper.find(byTestid('publish-next-btn')).trigger('click');
    expect(wrapper.find(byTestid('publish-step-confirm')).exists()).toBe(true);
    expect(wrapper.text()).toContain('番茄小说');
    expect(wrapper.text()).toContain('已填写');
  });

  it('retreats with prev button and closes from header', async () => {
    const pt = makeProductToolsContext();
    await pt.openPublishWizard();
    const { wrapper } = mountPublishModal(pt);

    pt.nextPublishStep();
    await flushPromises();
    await wrapper.find(byTestid('publish-prev-btn')).trigger('click');
    expect(pt.publishStep).toBe(0);

    await wrapper.find(byTestid('publish-modal-close')).trigger('click');
    expect(pt.publishModalOpen).toBe(false);
  });

  it('submits publish and shows success message', async () => {
    const pt = makeProductToolsContext();
    await pt.openPublishWizard();
    pt.publishStep = 3;
    const { wrapper } = mountPublishModal(pt);

    await wrapper.find(byTestid('publish-submit-btn')).trigger('click');
    await flushPromises();
    expect(apiMocks.submitCreatorPublish).toHaveBeenCalled();
    expect(wrapper.find(byTestid('publish-success-msg')).text()).toContain('已提交');
  });

  it('opens export modal from format step', async () => {
    const pt = makeProductToolsContext();
    const openExportModal = vi.fn();
    pt.openExportModal = openExportModal;
    await pt.openPublishWizard();
    pt.publishStep = 1;
    const { wrapper } = mountPublishModal(pt);

    await wrapper.find(byTestid('publish-open-export')).trigger('click');
    expect(pt.publishModalOpen).toBe(false);
    expect(openExportModal).toHaveBeenCalledWith('submission');
  });

  it('shows publish history snippet when entries exist', async () => {
    apiMocks.fetchCreatorPublishHistory.mockResolvedValue({
      slug: 'demo-novel',
      entries: [
        { id: '1', created_at: '2026-07-01', platform: 'fanqie', status: 'queued', adapter_id: 'stub' },
        { id: '2', created_at: '2026-07-02', platform: 'qidian', status: 'failed', adapter_id: 'stub' },
      ],
    });
    const pt = makeProductToolsContext();
    await pt.openPublishWizard();
    const { wrapper } = mountPublishModal(pt);
    expect(wrapper.find(byTestid('publish-history')).exists()).toBe(true);
    expect(wrapper.find(byTestid('publish-history-open-all')).text()).toContain('2');
  });
});
