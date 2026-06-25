// tests/unit/use-creator-page.spec.ts — useCreatorPage refresh 编排

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { defineComponent, ref } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';

const pageMocks = vi.hoisted(() => ({
  fetchCreatorOverview: vi.fn(),
  loadVolumePlan: vi.fn(),
  loadSettingsDocs: vi.fn(),
  loadSettingsHistory: vi.fn(),
  loadVolumeTemplates: vi.fn(),
  loadTemplateSyncSources: vi.fn(),
  loadOnboardingWizard: vi.fn(),
  pollBatchJob: vi.fn(),
  loadMergePreferences: vi.fn(),
  loadMergePresetPackages: vi.fn(),
  loadTemplateApprovals: vi.fn(),
  loadBatchHistory: vi.fn(),
  loadDiffCollabNotes: vi.fn(),
  refreshVolumePlanDiffPreview: vi.fn(),
  tryLoadVolumePlanDiffShareLinkPreview: vi.fn(),
  resumeBatchPollingIfNeeded: vi.fn(),
  maybeAutoSelectWritingChapter: vi.fn(),
  syncWizardPanelOpen: vi.fn(),
  loadCreationModeSwitchHistory: vi.fn(),
  parallelStarted: [] as string[],
}));

function trackParallel(name: string, impl: () => Promise<unknown> = async () => undefined) {
  return vi.fn(async () => {
    pageMocks.parallelStarted.push(name);
    return impl();
  });
}

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorOverview: (...args: unknown[]) => pageMocks.fetchCreatorOverview(...args),
  runCreatorLogicCheck: vi.fn(),
}));

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({ projectRevision: ref(0) }),
}));

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    focusWizard: ref(false),
    focusWizardStep: ref(null),
    focusWizardDone: ref([]),
    focusWizardNotes: ref({}),
    setWizardDeepLink: vi.fn(),
    buildWizardShareUrl: vi.fn(),
    navigateTo: vi.fn(),
    focusCreatorWorkspace: ref(null),
    setCreatorWorkspace: vi.fn(),
  }),
}));

vi.mock('../../src/composables/useCreatorOnboarding.js', () => ({
  useCreatorOnboarding: () => ({
    panelContext: {},
    onboardingWizard: ref(null),
    linkModeToOnboardingStep: vi.fn(),
    wizardEmailTo: ref(''),
    loadOnboardingWizard: pageMocks.loadOnboardingWizard,
    syncWizardPanelOpen: pageMocks.syncWizardPanelOpen,
  }),
}));

vi.mock('../../src/composables/useCreatorAdvanceBatch.js', () => ({
  useCreatorAdvanceBatch: () => ({
    panelContext: {},
    batchStart: ref(1),
    batchEnd: ref(10),
    batchBudget: ref(0.3),
    pollBatchJob: pageMocks.pollBatchJob,
    resumeBatchPollingIfNeeded: pageMocks.resumeBatchPollingIfNeeded,
  }),
}));

vi.mock('../../src/composables/useCreatorBatchHistory.js', () => ({
  useCreatorBatchHistory: () => ({
    panelContext: {},
    loadBatchHistory: pageMocks.loadBatchHistory,
  }),
}));

vi.mock('../../src/composables/useCreatorVolumePlan.js', () => ({
  useCreatorVolumePlan: () => ({
    panelContext: {},
    editableVolumes: ref([]),
    loadVolumePlan: pageMocks.loadVolumePlan,
    loadVolumeTemplates: pageMocks.loadVolumeTemplates,
    loadTemplateSyncSources: pageMocks.loadTemplateSyncSources,
    loadTemplateApprovals: pageMocks.loadTemplateApprovals,
    loadDiffCollabNotes: pageMocks.loadDiffCollabNotes,
    refreshVolumePlanDiffPreview: pageMocks.refreshVolumePlanDiffPreview,
    tryLoadVolumePlanDiffShareLinkPreview: pageMocks.tryLoadVolumePlanDiffShareLinkPreview,
  }),
}));

vi.mock('../../src/composables/useCreatorModeGuide.js', () => ({
  useCreatorModeGuide: () => ({
    panelContext: {},
    loadCreationModeSwitchHistory: pageMocks.loadCreationModeSwitchHistory,
    onCreationModeSwitchHotkey: vi.fn(),
  }),
}));

vi.mock('../../src/composables/useCreatorWrite.js', () => ({
  useCreatorWrite: () => ({
    panelContext: {},
    maybeAutoSelectWritingChapter: pageMocks.maybeAutoSelectWritingChapter,
    activeLogicCheckIssueIdx: ref(null),
    handleLogicCheckIssueClick: vi.fn(),
    onLogicCheckIssueKeydown: vi.fn(),
    scrollToBatchDeviationList: vi.fn(),
    openFirstBatchDeviationChapter: vi.fn(),
    updateBatchDeviationInlineSummary: vi.fn(),
    linkBatchDeviationInlineSummary: vi.fn(),
    handleDeviationClick: vi.fn(),
    jumpToChapter: vi.fn(),
  }),
}));

vi.mock('../../src/composables/useCreatorPulse.js', () => ({
  useCreatorPulse: () => ({
    panelContext: {},
    onBatchCompleted: vi.fn(),
    setBatchSummaryPrompt: vi.fn(),
  }),
}));

vi.mock('../../src/composables/useCreatorSettings.js', () => ({
  useCreatorSettings: () => ({
    panelContext: {},
    loadSettingsDocs: pageMocks.loadSettingsDocs,
    loadSettingsHistory: pageMocks.loadSettingsHistory,
    loadMergePreferences: pageMocks.loadMergePreferences,
    loadMergePresetPackages: pageMocks.loadMergePresetPackages,
  }),
}));

describe('useCreatorPage', () => {
  beforeEach(() => {
    vi.resetModules();
    pageMocks.parallelStarted = [];
    pageMocks.fetchCreatorOverview.mockImplementation(trackParallel('overview', async () => ({
      creation_mode: 'companion',
      chapters: [],
      ui_profile: { creator_workspace_tabs: true },
    })));
    pageMocks.loadVolumePlan.mockImplementation(trackParallel('loadVolumePlan'));
    pageMocks.loadSettingsDocs.mockImplementation(trackParallel('loadSettingsDocs'));
    pageMocks.loadSettingsHistory.mockImplementation(trackParallel('loadSettingsHistory'));
    pageMocks.loadVolumeTemplates.mockImplementation(trackParallel('loadVolumeTemplates'));
    pageMocks.loadTemplateSyncSources.mockImplementation(trackParallel('loadTemplateSyncSources'));
    pageMocks.loadOnboardingWizard.mockImplementation(trackParallel('loadOnboardingWizard'));
    pageMocks.pollBatchJob.mockImplementation(trackParallel('pollBatchJob'));
    pageMocks.loadMergePreferences.mockImplementation(trackParallel('loadMergePreferences'));
    pageMocks.loadMergePresetPackages.mockImplementation(trackParallel('loadMergePresetPackages'));
    pageMocks.loadTemplateApprovals.mockImplementation(trackParallel('loadTemplateApprovals'));
    pageMocks.loadBatchHistory.mockImplementation(trackParallel('loadBatchHistory'));
    pageMocks.loadDiffCollabNotes.mockImplementation(trackParallel('loadDiffCollabNotes'));
    pageMocks.refreshVolumePlanDiffPreview.mockResolvedValue(undefined);
    pageMocks.tryLoadVolumePlanDiffShareLinkPreview.mockImplementation(() => undefined);
    pageMocks.resumeBatchPollingIfNeeded.mockImplementation(() => undefined);
    pageMocks.maybeAutoSelectWritingChapter.mockImplementation(() => undefined);
    pageMocks.syncWizardPanelOpen.mockImplementation(() => undefined);
    pageMocks.loadCreationModeSwitchHistory.mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  async function mountPageHost() {
    const { useCreatorPage } = await import('../../src/composables/useCreatorPage.js');
    let page: ReturnType<typeof useCreatorPage> | null = null;
    const Host = defineComponent({
      name: 'CreatorPageHost',
      setup() {
        page = useCreatorPage();
        return () => null;
      },
    });
    mount(Host);
    await flushPromises();
    return page!;
  }

  test('refresh kicks off overview fetch in parallel with hub loaders', async () => {
    const page = await mountPageHost();
    pageMocks.parallelStarted = [];
    await page.refresh();
    await flushPromises();

    expect(pageMocks.fetchCreatorOverview).toHaveBeenCalledTimes(2);
    expect(pageMocks.loadVolumePlan).toHaveBeenCalled();
    expect(pageMocks.loadSettingsDocs).toHaveBeenCalled();
    expect(pageMocks.loadOnboardingWizard).toHaveBeenCalled();
    expect(pageMocks.pollBatchJob).toHaveBeenCalled();
    expect(pageMocks.parallelStarted).toContain('overview');
    expect(pageMocks.parallelStarted).toContain('loadVolumePlan');
    expect(pageMocks.parallelStarted).toContain('loadSettingsDocs');
  });

  test('refresh sets overview and clears loading on success', async () => {
    const page = await mountPageHost();
    expect(page.loading.value).toBe(false);
    await page.refresh();
    expect(page.overview.value?.creation_mode).toBe('companion');
    expect(page.loading.value).toBe(false);
    expect(page.error.value).toBeNull();
  });

  test('refresh records API errors', async () => {
    const page = await mountPageHost();
    pageMocks.fetchCreatorOverview.mockRejectedValueOnce(new Error('network down'));
    await page.refresh();
    expect(page.error.value).toBe('network down');
    expect(page.loading.value).toBe(false);
  });

  test('exposes workspace tab badges from deviation count', async () => {
    pageMocks.fetchCreatorOverview.mockImplementation(async () => ({
      creation_mode: 'companion',
      chapters: [],
      deviation_count: 3,
      ui_profile: { creator_workspace_tabs: true, deviation_min_severity: null },
    }));
    const page = await mountPageHost();
    expect(page.workspaceTabBadges.value).toEqual({ pulse: 3 });
  });
});
