// tests/unit/creator-product-tools.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, computed } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorPreferencesSection from '../../src/components/creator/CreatorPreferencesSection.vue';
import CreatorStructureGraph from '../../src/components/creator/CreatorStructureGraph.vue';
import CreatorExportModal from '../../src/components/creator/CreatorExportModal.vue';
import CreatorInterventionBanner from '../../src/components/creator/CreatorInterventionBanner.vue';
import { CREATOR_PRODUCT_TOOLS_KEY, createCreatorProductToolsContext } from '../../src/components/creator/creatorProductToolsKey.js';
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

function makeProductToolsContext(overrides: Record<string, unknown> = {}) {
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
    visibleDeviations: computed(() => [{ severity: 'alert', chapter: 2, message: '缺正文' }]),
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
    ...overrides,
  });
  return createCreatorProductToolsContext(panelContext) as ReturnType<typeof createCreatorProductToolsContext> & {
    preferences: { defaultModel?: string; taskModels: { body: string }; memoryRagEnabled: boolean; interventionRules: Record<string, boolean> };
    preferencesSummary: string;
    interventionItems: Array<{ id: string }>;
    loadMemoryAssets: () => Promise<void>;
    runMemorySearch: () => Promise<void>;
    memorySearchQuery: string;
    memorySearchResults: unknown[];
    memorySearchRan: boolean;
    toggleMemoryPin: (asset: { id: string; pinned: boolean; placeholder: boolean }) => Promise<void>;
    refreshExportPreview: () => Promise<void>;
    exportPreview: string;
    focusMemoryEntity: (entity: { id?: string; kind?: string; name?: string } | null) => void;
    goToSettingsForAsset: (item: { editable?: boolean }) => void;
    nextPublishStep: () => void;
    prevPublishStep: () => void;
    publishStep: number;
    preferencesSavedHint: string;
    prefillPublishFromSubmission: () => Promise<void>;
    publishPackPreview: string;
    publishSubmissionChapters: number[];
    handleInterventionAction: (item: { action: string; chapter?: number }) => Promise<void>;
    loadPreferencesFromServer: () => Promise<void>;
    loadCreatorModels: () => Promise<void>;
    creatorModelOptions: Array<{ id: string; label: string }>;
    structureGraph: { volumes: unknown[] };
    runExportEpub: () => Promise<void>;
    runExportDocx: () => Promise<void>;
    openPublishWizard: () => Promise<void>;
    submitPublish: () => Promise<void>;
    savePreferences: () => Promise<void>;
    memoryAssetsFiltered: unknown[];
    memoryFilter: string;
    exportMode: string;
  };
}

describe('creator product tools', () => {
  beforeEach(() => {
    apiMocks.fetchChapters.mockReset();
    apiMocks.fetchCreatorChapterPreview.mockReset();
    apiMocks.fetchCreatorPreferences.mockReset();
    apiMocks.saveCreatorPreferencesApi.mockReset();
    apiMocks.fetchCreatorMemoryAssets.mockReset();
    apiMocks.exportCreatorEpub.mockReset();
    apiMocks.fetchCreatorPublishHistory.mockResolvedValue({ slug: 'demo-novel', entries: [] });
    apiMocks.fetchCreatorPublishPlatforms.mockResolvedValue({
      slug: 'demo-novel',
      platforms: [
        { id: 'fanqie', label: '番茄小说', connection: 'stub', capabilities: { oauth_required: true, max_intro_chars: 500 } },
      ],
    });
    apiMocks.fetchCreatorModels.mockResolvedValue({
      models: [
        { id: 'gpt-4o', label: 'GPT-4o', provider: 'openai', available: true },
        { id: 'local-mock', label: '本地 Mock', provider: 'mock', available: true },
      ],
      default_model: 'gpt-4o',
    });
    localStorage.clear();
  });

  it('CreatorPreferencesSection saves preferences', async () => {
    const pt = makeProductToolsContext();
    const wrapper = mount(CreatorPreferencesSection, {
      global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
    });
    await wrapper.find(byTestid('pref-save-btn')).trigger('click');
    await flushPromises();
    expect(apiMocks.saveCreatorPreferencesApi).toHaveBeenCalled();
    expect(pt.preferencesSavedHint).toContain('同步');
  });

  it('CreatorStructureGraph switches to timeline view', async () => {
    const pt = makeProductToolsContext();
    const wrapper = mount(CreatorStructureGraph, {
      global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
    });
    await wrapper.find(byTestid('structure-view-timeline')).trigger('click');
    expect(wrapper.find(byTestid('structure-timeline')).exists()).toBe(true);
    await wrapper.find(byTestid('structure-view-tree')).trigger('click');
    expect(wrapper.find(byTestid('structure-chapter-1')).exists()).toBe(true);
  });

  it('CreatorPreferencesSection toggles intervention rule', async () => {
    const pt = makeProductToolsContext();
    const wrapper = mount(CreatorPreferencesSection, {
      global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
    });
    const logicRule = wrapper.find(byTestid('pref-intervention-logicP0'));
    expect(logicRule.exists()).toBe(true);
    await logicRule.setValue(false);
    expect(pt.preferences.interventionRules.logicP0).toBe(false);
  });

  it('CreatorStructureGraph renders volume chapters', () => {
    const pt = makeProductToolsContext();
    const wrapper = mount(CreatorStructureGraph, {
      global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
    });
    expect(wrapper.find(byTestid('structure-chapter-1')).exists()).toBe(true);
    expect(wrapper.find(byTestid('structure-chapter-2')).exists()).toBe(true);
    expect(wrapper.find(byTestid('structure-view-timeline')).exists()).toBe(true);
  });

  it('export modal preview builds markdown', async () => {
    const pt = makeProductToolsContext();
    pt.exportModalOpen = true;
    apiMocks.fetchChapters.mockResolvedValue({
      chapters: [{ chapter: 1, has_body: true }],
    });
    apiMocks.fetchCreatorChapterPreview.mockResolvedValue({
      title: '第一章',
      body: '正文',
    });
    const wrapper = mount(CreatorExportModal, {
      global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
    });
    await wrapper.find(byTestid('export-preview-btn')).trigger('click');
    await flushPromises();
    expect(pt.exportPreview).toContain('第一章');
    expect(pt.exportPreview).toContain('正文');
  });

  it('interventionItems surfaces batch progress and logic p0', () => {
    const pt = makeProductToolsContext({
      batchRunning: ref(true),
      batchJob: ref({ status: 'running', message: '批量中' }),
      logicCheckResult: ref({
        chapter: 2,
        issues: [{ severity: 'P0', message: '时间线' }],
      }),
    });
    expect(pt.interventionItems.some((i) => i.id === 'batch-running')).toBe(true);
    expect(pt.interventionItems.some((i) => i.id === 'logic-p0')).toBe(true);
  });

  it('interventionItems surfaces preferences unsaved', () => {
    const pt = makeProductToolsContext();
    pt.preferencesDirty = true;
    expect(pt.interventionItems.some((i) => i.id === 'preferences-unsaved')).toBe(true);
  });

  it('handleInterventionAction routes to workspace tabs', async () => {
    const setWorkspaceTab = vi.fn();
    const jumpToChapter = vi.fn(async () => undefined);
    const navigateTo = vi.fn();
    const pt = makeProductToolsContext({ setWorkspaceTab, jumpToChapter, navigateTo });
    await pt.handleInterventionAction({ action: 'pulse', chapter: 3 });
    await pt.handleInterventionAction({ action: 'write', chapter: 1 });
    await pt.handleInterventionAction({ action: 'memory' });
    await pt.handleInterventionAction({ action: 'settings' });
    await pt.handleInterventionAction({ action: 'decisions' });
    expect(setWorkspaceTab).toHaveBeenCalledWith('pulse');
    expect(jumpToChapter).toHaveBeenCalledWith(3);
    expect(navigateTo).toHaveBeenCalledWith('decisions', { clearFocus: true });
  });

  it('CreatorInterventionBanner renders items and handles action click', async () => {
    const pt = makeProductToolsContext();
    pt.handleInterventionAction = vi.fn();
    const wrapper = mount(CreatorInterventionBanner, {
      global: { provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt } },
    });
    expect(wrapper.find(byTestid('creator-intervention-banner')).exists()).toBe(true);
    await wrapper.find(byTestid('intervention-action-deviation-alerts')).trigger('click');
    expect(pt.handleInterventionAction).toHaveBeenCalled();
  });

  it('loadPreferencesFromServer hydrates from API', async () => {
    apiMocks.fetchCreatorPreferences.mockResolvedValue({
      default_model: 'gpt-4o',
      intervention_rules: { logic_p0: false },
    });
    const pt = makeProductToolsContext();
    await pt.loadPreferencesFromServer();
    expect(pt.preferences.defaultModel).toBe('gpt-4o');
    expect(pt.preferences.interventionRules.logicP0).toBe(false);
  });

  it('loadCreatorModels falls back when API fails', async () => {
    apiMocks.fetchCreatorModels.mockRejectedValueOnce(new Error('down'));
    const pt = makeProductToolsContext();
    await pt.loadCreatorModels();
    expect(pt.creatorModelOptions.length).toBeGreaterThan(0);
  });

  it('structureGraph exposes volume nodes from overview', () => {
    const pt = makeProductToolsContext();
    expect(pt.structureGraph.volumes.length).toBeGreaterThan(0);
  });

  it('interventionItems surfaces alert deviations', () => {
    const pt = makeProductToolsContext();
    expect(pt.interventionItems.some((i) => i.id === 'deviation-alerts')).toBe(true);
  });

  it('preferencesSummary reflects body task model', () => {
    const pt = makeProductToolsContext();
    pt.preferences.taskModels.body = 'gpt-4o';
    expect(pt.preferencesSummary).toContain('GPT-4o');
  });

  it('interventionItems surfaces settings unsaved', () => {
    const pt = makeProductToolsContext({
      settingsHasUnsavedChanges: computed(() => true),
    });
    expect(pt.interventionItems.some((i) => i.id === 'settings-unsaved')).toBe(true);
  });

  it('interventionItems surfaces memory offline when RAG on', async () => {
    const pt = makeProductToolsContext();
    pt.preferences.memoryRagEnabled = true;
    apiMocks.fetchCreatorMemoryAssets.mockResolvedValue({
      memory_available: false,
      memory_rag_enabled: true,
      items: [],
    });
    await pt.loadMemoryAssets();
    expect(pt.interventionItems.some((i) => i.id === 'memory-offline')).toBe(true);
  });

  it('runMemorySearch stores results', async () => {
    const pt = makeProductToolsContext();
    pt.memorySearchQuery = '主角';
    apiMocks.queryCreatorMemory.mockResolvedValue({
      query: '主角',
      memory_available: false,
      used_fallback: true,
      results: [{ id: 'x', snippet: '片段', score: 0.8, chapter: 1, kind: 'memory', source: 'local' }],
    });
    await pt.runMemorySearch();
    expect(pt.memorySearchResults).toHaveLength(1);
    expect(pt.memorySearchRan).toBe(true);
  });

  it('interventionItems respects disabled rules', () => {
    const pt = makeProductToolsContext();
    pt.preferences.interventionRules.deviationAlerts = false;
    expect(pt.interventionItems.some((i) => i.id === 'deviation-alerts')).toBe(false);
  });

  it('toggleMemoryPin calls annotation API', async () => {
    const pt = makeProductToolsContext();
    apiMocks.saveCreatorMemoryAnnotation.mockResolvedValue({
      asset_id: 'memory-ch-1',
      pinned: true,
    });
    apiMocks.fetchCreatorMemoryAssets.mockResolvedValue({
      memory_available: true,
      items: [{ id: 'memory-ch-1', kind: 'memory', name: '片段', excerpt: 'x', pinned: true }],
    });
    await pt.toggleMemoryPin({ id: 'memory-ch-1', pinned: false, placeholder: false });
    expect(apiMocks.saveCreatorMemoryAnnotation).toHaveBeenCalledWith('memory-ch-1', { pinned: true });
  });

  it('prefillPublishFromSubmission builds pack preview', async () => {
    const pt = makeProductToolsContext();
    apiMocks.fetchChapters.mockResolvedValue({
      chapters: [{ chapter: 1, has_body: true }],
    });
    apiMocks.fetchCreatorChapterPreview.mockResolvedValue({
      title: '第一章',
      body_text: '正文',
    });
    await pt.prefillPublishFromSubmission();
    expect(pt.publishPackPreview).toContain('投稿包');
    expect(pt.publishSubmissionChapters).toEqual([1]);
  });

  it('runExportEpub and runExportDocx download blobs', async () => {
    const pt = makeProductToolsContext();
    pt.exportModalOpen = true;
    const blob = new Blob(['x']);
    apiMocks.exportCreatorEpub.mockResolvedValue(blob);
    apiMocks.exportCreatorDocx.mockResolvedValue(blob);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    await pt.runExportEpub();
    await pt.runExportDocx();
    expect(apiMocks.exportCreatorEpub).toHaveBeenCalled();
    expect(apiMocks.exportCreatorDocx).toHaveBeenCalled();
    clickSpy.mockRestore();
  });

  it('savePreferences falls back to local when API fails', async () => {
    apiMocks.saveCreatorPreferencesApi.mockRejectedValueOnce(new Error('offline'));
    const pt = makeProductToolsContext();
    await pt.savePreferences();
    expect(pt.preferencesSavedHint).toContain('本机');
  });

  it('openPublishWizard and submitPublish update status', async () => {
    apiMocks.submitCreatorPublish.mockResolvedValue({
      message: '已提交',
      status: 'queued',
    });
    const pt = makeProductToolsContext();
    await pt.openPublishWizard();
    await pt.submitPublish();
    expect(pt.publishMessage).toContain('已提交');
  });

  it('memoryAssetsFiltered respects memory filter', async () => {
    const pt = makeProductToolsContext();
    apiMocks.fetchCreatorMemoryAssets.mockResolvedValue({
      memory_available: true,
      items: [
        { id: '1', kind: 'memory', name: 'a', excerpt: 'x' },
        { id: '2', kind: 'character', name: 'b', excerpt: 'y' },
      ],
    });
    await pt.loadMemoryAssets();
    pt.memoryFilter = 'character';
    expect(pt.memoryAssetsFiltered).toHaveLength(1);
  });

  it('runMemorySearch records API errors', async () => {
    const pt = makeProductToolsContext();
    pt.memorySearchQuery = '主角';
    apiMocks.queryCreatorMemory.mockRejectedValueOnce(new Error('search down'));
    await pt.runMemorySearch();
    expect(pt.memorySearchRan).toBe(true);
    expect(pt.memorySearchResults).toEqual([]);
  });

  it('interventionItems shows empty write hint for studio mode', () => {
    const pt = makeProductToolsContext({
      overview: ref({
        max_chapter: 5,
        chapters_written: 0,
        creation_mode: 'studio',
        chapters: [],
      }),
      visibleDeviations: computed(() => []),
    });
    expect(pt.interventionItems.some((i) => i.id === 'onboarding-write')).toBe(true);
  });

  it('refreshExportPreview supports range export mode', async () => {
    const pt = makeProductToolsContext();
    pt.exportMode = 'range';
    pt.exportRangeStart = 1;
    pt.exportRangeEnd = 1;
    apiMocks.fetchCreatorChapterPreview.mockResolvedValue({
      title: '第一章',
      body_text: '正文',
    });
    await pt.refreshExportPreview();
    expect(pt.exportPreview).toContain('第一章');
  });

  it('focusMemoryEntity and goToSettingsForAsset switch tabs', () => {
    const setWorkspaceTab = vi.fn();
    const pt = makeProductToolsContext({ setWorkspaceTab });
    pt.focusMemoryEntity({ id: 'e1', kind: 'foreshadow', name: '伏笔：测试' });
    expect(setWorkspaceTab).toHaveBeenCalledWith('memory');
    pt.goToSettingsForAsset({ editable: true });
    expect(setWorkspaceTab).toHaveBeenCalledWith('settings');
  });

  it('publish wizard steps advance and retreat', async () => {
    const pt = makeProductToolsContext();
    apiMocks.fetchChapters.mockResolvedValue({ chapters: [{ chapter: 1, has_body: true }] });
    apiMocks.fetchCreatorChapterPreview.mockResolvedValue({ title: '第一章', body_text: '正文' });
    await pt.openPublishWizard();
    pt.nextPublishStep();
    expect(pt.publishStep).toBeGreaterThan(0);
    pt.prevPublishStep();
    expect(pt.publishStep).toBe(0);
  });
});