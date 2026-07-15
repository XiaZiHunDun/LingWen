// tests/unit/creator-export-modal.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, computed } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorExportModal from '../../src/components/creator/CreatorExportModal.vue';
import { CREATOR_PRODUCT_TOOLS_KEY, createCreatorProductToolsContext } from '../../src/components/creator/creatorProductToolsKey.js';
import { useCreatorProductTools } from '../../src/composables/useCreatorProductTools.js';
import { byTestid } from '../helpers/by-testid';

vi.mock('../../src/api/index.js', () => ({
  fetchChapters: vi.fn().mockResolvedValue({ chapters: [{ chapter: 1, has_body: true }] }),
  fetchCreatorChapterPreview: vi.fn().mockResolvedValue({ title: '第一章', body: '正文' }),
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

function mountExportModal(overrides: Record<string, unknown> = {}) {
  const overview = ref({
    max_chapter: 10,
    chapters_written: 2,
    chapters: [{ chapter: 1, has_body: true }],
    pillars_excerpt: '支柱',
    global_outline_excerpt: '大纲',
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
    ...overrides,
  });
  const pt = createCreatorProductToolsContext(panelContext);
  pt.exportModalOpen = true;
  const wrapper = mount(CreatorExportModal, {
    global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
  });
  return { wrapper, pt };
}

describe('CreatorExportModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders export modal with default full mode', () => {
    const { wrapper } = mountExportModal();
    expect(wrapper.find(byTestid('creator-export-modal')).exists()).toBe(true);
    expect(wrapper.find(byTestid('export-mode-full')).exists()).toBe(true);
    expect(wrapper.find(byTestid('export-author')).exists()).toBe(true);
  });

  it('shows range inputs when range mode selected', async () => {
    const { wrapper, pt } = mountExportModal();
    pt.exportMode = 'range';
    await wrapper.vm.$nextTick();
    expect(wrapper.find(byTestid('export-range-start')).exists()).toBe(true);
    expect(wrapper.find(byTestid('export-range-end')).exists()).toBe(true);
  });

  it('shows submission fields when submission mode selected', async () => {
    const { wrapper, pt } = mountExportModal();
    pt.exportMode = 'submission';
    await wrapper.vm.$nextTick();
    expect(wrapper.find(byTestid('export-submission-sample-count')).exists()).toBe(true);
    expect(wrapper.find(byTestid('export-submission-intro')).exists()).toBe(true);
  });

  it('closes modal via close button', async () => {
    const { wrapper, pt } = mountExportModal();
    pt.closeExportModal = vi.fn();
    await wrapper.find(byTestid('export-modal-close')).trigger('click');
    expect(pt.closeExportModal).toHaveBeenCalled();
  });

  it('preview button triggers refreshExportPreview', async () => {
    const { wrapper, pt } = mountExportModal();
    pt.refreshExportPreview = vi.fn(async () => {
      pt.exportPreview = '# 预览';
    });
    await wrapper.find(byTestid('export-preview-btn')).trigger('click');
    await flushPromises();
    expect(pt.refreshExportPreview).toHaveBeenCalled();
  });

  it('download buttons delegate to product tools handlers', async () => {
    const { wrapper, pt } = mountExportModal();
    pt.runExportDownload = vi.fn();
    pt.runExportEpub = vi.fn();
    pt.runExportDocx = vi.fn();
    await wrapper.find(byTestid('export-download-btn')).trigger('click');
    await wrapper.find(byTestid('export-epub-btn')).trigger('click');
    await wrapper.find(byTestid('export-docx-btn')).trigger('click');
    expect(pt.runExportDownload).toHaveBeenCalled();
    expect(pt.runExportEpub).toHaveBeenCalled();
    expect(pt.runExportDocx).toHaveBeenCalled();
  });

  it('disables actions when exportBusy', async () => {
    const { wrapper, pt } = mountExportModal();
    pt.exportBusy = true;
    await wrapper.vm.$nextTick();
    expect(wrapper.find(byTestid('export-preview-btn')).attributes('disabled')).toBeDefined();
  });
});
