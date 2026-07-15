// tests/unit/creator-publish-history-modal.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { ref, computed } from 'vue';
import { mount } from '@vue/test-utils';
import CreatorPublishHistoryModal from '../../src/components/creator/CreatorPublishHistoryModal.vue';
import { CREATOR_PRODUCT_TOOLS_KEY, createCreatorProductToolsContext } from '../../src/components/creator/creatorProductToolsKey.js';
import { useCreatorProductTools } from '../../src/composables/useCreatorProductTools.js';
import { byTestid } from '../helpers/by-testid';

vi.mock('../../src/api/index.js', () => ({
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

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({ activeSlug: ref('demo-novel') }),
}));

function mountHistoryModal(history: unknown[] = []) {
  const overview = ref({
    max_chapter: 5,
    chapters_written: 1,
    chapters: [{ chapter: 1, has_body: true }],
    pillars_excerpt: '',
    global_outline_excerpt: '',
  });
  const { panelContext } = useCreatorProductTools({
    overview,
    error: ref(null),
    saveMessage: ref(''),
    visibleDeviations: computed(() => []),
    editableVolumes: ref([]),
    pillarsText: ref(''),
    globalOutlineText: ref(''),
    logicCheckResult: ref(null),
    batchJob: ref(null),
    batchRunning: ref(false),
    isWorkspaceColumnVisible: () => true,
    setWorkspaceTab: vi.fn(),
    jumpToChapter: vi.fn(),
    navigateTo: vi.fn(),
    settingsHasUnsavedChanges: computed(() => false),
  });
  const pt = createCreatorProductToolsContext(panelContext);
  pt.publishHistoryModalOpen = true;
  pt.publishHistory = history;
  const wrapper = mount(CreatorPublishHistoryModal, {
    global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
  });
  return { wrapper, pt };
}

describe('CreatorPublishHistoryModal', () => {
  it('renders empty state when no history', () => {
    const { wrapper } = mountHistoryModal([]);
    expect(wrapper.find(byTestid('publish-history-empty')).exists()).toBe(true);
    expect(wrapper.text()).toContain('暂无发布记录');
  });

  it('renders history rows with platform and status', () => {
    const { wrapper } = mountHistoryModal([
      {
        id: 'pub-1',
        platform: '番茄',
        status: 'queued',
        created_at: '2026-07-08',
        message: '已排队',
        adapter_id: 'stub',
        intro: '简介文本',
      },
    ]);
    expect(wrapper.find(byTestid('publish-history-list')).exists()).toBe(true);
    expect(wrapper.find(byTestid('publish-history-row-pub-1')).exists()).toBe(true);
    expect(wrapper.text()).toContain('番茄');
    expect(wrapper.text()).toContain('queued');
  });

  it('closes modal via close button', async () => {
    const { wrapper, pt } = mountHistoryModal([]);
    pt.closePublishHistoryModal = vi.fn();
    await wrapper.find(byTestid('publish-history-close')).trigger('click');
    expect(pt.closePublishHistoryModal).toHaveBeenCalled();
  });

  it('does not render when modal closed', () => {
    const { wrapper, pt } = mountHistoryModal([]);
    pt.publishHistoryModalOpen = false;
    return wrapper.vm.$nextTick().then(() => {
      expect(wrapper.find(byTestid('creator-publish-history-modal')).exists()).toBe(false);
    });
  });
});
