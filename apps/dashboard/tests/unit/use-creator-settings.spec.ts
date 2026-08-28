// tests/unit/use-creator-settings.spec.ts — useCreatorSettings 编排
//
// Phase 126 v16.2.2 T4a: main-file composable refactor — 5 docs/history
// functions now use typed wrapper (`@/api/settings`). Submodule mocks stay
// on the legacy path (T4b carryover).

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, ref } from 'vue';
import { flushPromises } from '@vue/test-utils';

const settingsMocks = vi.hoisted(() => ({
  // Legacy mocks (kept for any consumers still using Creator-prefixed names
  // via the @/api/index.js barrel — back-compat alias to same vi.fn instance)
  fetchCreatorSettingsDocs: vi.fn(),
  // Back-compat alias (test body still uses Creator-prefixed names):
  fetchCreatorSettingsHistory: vi.fn(),
  saveCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsThreeWay: vi.fn(),
  previewCreatorSettingsMerge: vi.fn(),
  // Typed wrapper mocks (per v16.2.8 T4.5: useCreatorSettings.js main + submodule
  // both use unprefixed names from @/api/settings)
  fetchMergePreferences: vi.fn(),
  exportMergePreferences: vi.fn(),
  importMergePreferences: vi.fn(),
  fetchSettingsHistory: vi.fn(),
  restoreSettingsSnapshot: vi.fn(),
  preflightFactoryMergePresetPull: vi.fn(),
  fetchMergePresetChangelog: vi.fn(),
  fetchMergePresetChangelogDiff: vi.fn(),
  fetchMergePresetPackages: vi.fn(),
  fetchFactoryMergePresetPackages: vi.fn(),
  applyMergePresetConflictFix: vi.fn(),
  applyAllMergePresetConflictFixes: vi.fn(),
  preflightMergePresetImport: vi.fn(),
  previewMergePresetImportDiff: vi.fn(),
  applyToposortMergePresetOrder: vi.fn(),
  exportMergePresetPackages: vi.fn(),
  importMergePresetPackages: vi.fn(),
  publishMergePresetToFactory: vi.fn(),
  pullFactoryMergePresetsToProject: vi.fn(),
  // T4a typed wrapper mocks (used by main file's direct calls)
  saveSettingsDocs: vi.fn(),
  previewSettingsDocsDiff: vi.fn(),
  previewSettingsThreeWay: vi.fn(),
  fetchSettingsDocs: vi.fn(),
  previewSettingsMergeStrategy: vi.fn(),
}));

// Back-compat aliases for the legacy @/api/index.js barrel
vi.mock('../../src/api/index.js', () => ({
  fetchCreatorSettingsDocs: (...args: unknown[]) => settingsMocks.fetchCreatorSettingsDocs(...args),
  saveCreatorSettingsDocs: (...args: unknown[]) => settingsMocks.saveCreatorSettingsDocs(...args),
  previewCreatorSettingsDocs: (...args: unknown[]) => settingsMocks.previewCreatorSettingsDocs(...args),
  previewCreatorSettingsThreeWay: (...args: unknown[]) => settingsMocks.previewCreatorSettingsThreeWay(...args),
  previewCreatorSettingsMerge: (...args: unknown[]) => settingsMocks.previewCreatorSettingsMerge(...args),
  fetchCreatorMergePreferences: (...args: unknown[]) => settingsMocks.fetchMergePreferences(...args),
  exportCreatorMergePreferences: (...args: unknown[]) => settingsMocks.exportMergePreferences(...args),
  importCreatorMergePreferences: (...args: unknown[]) => settingsMocks.importMergePreferences(...args),
  fetchCreatorSettingsHistory: (...args: unknown[]) => settingsMocks.fetchSettingsHistory(...args),
  restoreCreatorSettingsSnapshot: (...args: unknown[]) => settingsMocks.restoreSettingsSnapshot(...args),
  preflightCreatorFactoryMergePresetPull: (...args: unknown[]) => settingsMocks.preflightFactoryMergePresetPull(...args),
  fetchCreatorMergePresetChangelog: (...args: unknown[]) => settingsMocks.fetchMergePresetChangelog(...args),
  fetchCreatorMergePresetChangelogDiff: (...args: unknown[]) => settingsMocks.fetchMergePresetChangelogDiff(...args),
  fetchCreatorMergePresetPackages: (...args: unknown[]) => settingsMocks.fetchMergePresetPackages(...args),
  fetchCreatorFactoryMergePresetPackages: (...args: unknown[]) => settingsMocks.fetchFactoryMergePresetPackages(...args),
  applyCreatorMergePresetConflictFix: (...args: unknown[]) => settingsMocks.applyMergePresetConflictFix(...args),
  applyAllCreatorMergePresetConflictFixes: (...args: unknown[]) => settingsMocks.applyAllMergePresetConflictFixes(...args),
  preflightCreatorMergePresetImport: (...args: unknown[]) => settingsMocks.preflightMergePresetImport(...args),
  previewCreatorMergePresetImportDiff: (...args: unknown[]) => settingsMocks.previewMergePresetImportDiff(...args),
  applyCreatorMergePresetToposort: (...args: unknown[]) => settingsMocks.applyToposortMergePresetOrder(...args),
  exportCreatorMergePresetPackages: (...args: unknown[]) => settingsMocks.exportMergePresetPackages(...args),
  importCreatorMergePresetPackages: (...args: unknown[]) => settingsMocks.importMergePresetPackages(...args),
  publishCreatorMergePresetToFactory: (...args: unknown[]) => settingsMocks.publishMergePresetToFactory(...args),
  pullCreatorFactoryMergePresetPackages: (...args: unknown[]) => settingsMocks.pullFactoryMergePresetsToProject(...args),
}));

// v16.2.8 T4.5: typed wrapper mock — unprefixed names (per v16.2.1+ convention).
// useCreatorSettings.js (main + submodule useMergePresets.ts) now imports these
// directly from @/api/settings.
vi.mock('../../src/api/settings.js', () => ({
  fetchSettingsHistory: (...args: unknown[]) => settingsMocks.fetchSettingsHistory(...args),
  restoreSettingsSnapshot: (...args: unknown[]) => settingsMocks.restoreSettingsSnapshot(...args),
  saveSettingsDocs: (...args: unknown[]) => settingsMocks.saveSettingsDocs(...args),
  previewSettingsDocsDiff: (...args: unknown[]) => settingsMocks.previewSettingsDocsDiff(...args),
  previewSettingsThreeWay: (...args: unknown[]) => settingsMocks.previewSettingsThreeWay(...args),
  fetchSettingsDocs: (...args: unknown[]) => settingsMocks.fetchSettingsDocs(...args),
  previewSettingsMergeStrategy: (...args: unknown[]) => settingsMocks.previewSettingsMergeStrategy(...args),
  fetchMergePreferences: (...args: unknown[]) => settingsMocks.fetchMergePreferences(...args),
  exportMergePreferences: (...args: unknown[]) => settingsMocks.exportMergePreferences(...args),
  importMergePreferences: (...args: unknown[]) => settingsMocks.importMergePreferences(...args),
  preflightFactoryMergePresetPull: (...args: unknown[]) => settingsMocks.preflightFactoryMergePresetPull(...args),
  fetchMergePresetChangelog: (...args: unknown[]) => settingsMocks.fetchMergePresetChangelog(...args),
  fetchMergePresetChangelogDiff: (...args: unknown[]) => settingsMocks.fetchMergePresetChangelogDiff(...args),
  fetchMergePresetPackages: (...args: unknown[]) => settingsMocks.fetchMergePresetPackages(...args),
  fetchFactoryMergePresetPackages: (...args: unknown[]) => settingsMocks.fetchFactoryMergePresetPackages(...args),
  applyMergePresetConflictFix: (...args: unknown[]) => settingsMocks.applyMergePresetConflictFix(...args),
  applyAllMergePresetConflictFixes: (...args: unknown[]) => settingsMocks.applyAllMergePresetConflictFixes(...args),
  preflightMergePresetImport: (...args: unknown[]) => settingsMocks.preflightMergePresetImport(...args),
  previewMergePresetImportDiff: (...args: unknown[]) => settingsMocks.previewMergePresetImportDiff(...args),
  applyToposortMergePresetOrder: (...args: unknown[]) => settingsMocks.applyToposortMergePresetOrder(...args),
  exportMergePresetPackages: (...args: unknown[]) => settingsMocks.exportMergePresetPackages(...args),
  importMergePresetPackages: (...args: unknown[]) => settingsMocks.importMergePresetPackages(...args),
  publishMergePresetToFactory: (...args: unknown[]) => settingsMocks.publishMergePresetToFactory(...args),
  pullFactoryMergePresetsToProject: (...args: unknown[]) => settingsMocks.pullFactoryMergePresetsToProject(...args),
}));

describe('useCreatorSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    settingsMocks.fetchCreatorSettingsDocs.mockResolvedValue({
      pillars_text: '支柱A',
      global_outline_text: '大纲A',
      pillars_revision: 'p1',
      global_outline_revision: 'o1',
    });
    settingsMocks.fetchCreatorSettingsHistory.mockResolvedValue({
      snapshots: [{ id: 'snap-1', recorded_at: '2026-06-01T00:00:00Z' }],
    });
    settingsMocks.previewCreatorSettingsDocs.mockResolvedValue({
      has_changes: true,
      pillars: { snippet: ['p'] },
      global_outline: { snippet: ['o'] },
    });
    settingsMocks.previewCreatorSettingsThreeWay.mockResolvedValue({
      has_changes: true,
      has_history: true,
      pillars: { snippet: ['p'] },
      global_outline: { snippet: ['o'] },
      disk_vs_history: { pillars: { changed: true } },
      editor_vs_history: { global_outline: { changed: false } },
    });
    settingsMocks.previewCreatorSettingsMerge.mockResolvedValue({
      pillars: { vs_disk: { snippet: ['merge'] } },
      global_outline: { vs_disk: { snippet: [] } },
    });
    settingsMocks.saveCreatorSettingsDocs.mockResolvedValue({});
    // T4a typed wrapper mock defaults (mirror legacy responses)
    settingsMocks.fetchSettingsHistory.mockResolvedValue({
      snapshots: [{ id: 'snap-1', recorded_at: '2026-06-01T00:00:00Z' }],
    });
    settingsMocks.previewSettingsThreeWay.mockResolvedValue({
      has_changes: true,
      has_history: true,
      pillars: { snippet: ['p'] },
      global_outline: { snippet: ['o'] },
      disk_vs_history: { pillars: { changed: true } },
      editor_vs_history: { global_outline: { changed: false } },
    });
    settingsMocks.previewSettingsDocsDiff.mockResolvedValue({
      has_changes: true,
      pillars: { snippet: ['p'] },
      global_outline: { snippet: ['o'] },
    });
    settingsMocks.saveSettingsDocs.mockResolvedValue({});
    // T4b: submodule's loadSettingsDocs + refreshMergeStrategyPreview now go
    // through typed wrapper. Defaults mirror legacy path responses.
    settingsMocks.fetchSettingsDocs.mockResolvedValue({
      pillars_text: '支柱A',
      global_outline_text: '大纲A',
      pillars_revision: 'p1',
      global_outline_revision: 'o1',
    });
    settingsMocks.previewSettingsMergeStrategy.mockResolvedValue({
      pillars: { vs_disk: { snippet: ['merge'] } },
      global_outline: { vs_disk: { snippet: [] } },
    });
    settingsMocks.fetchMergePreferences.mockResolvedValue({
      pillars_merge_source: 'editor',
      global_outline_merge_source: 'history',
      merge_snapshot_id: 'snap-1',
      uses_global_default: true,
    });
    settingsMocks.fetchMergePresetPackages.mockResolvedValue({
      packages: [
        {
          id: 'pkg-1',
          name: '项目预设',
          scope: 'project',
          builtin: false,
          pillars_merge_source: 'editor',
          global_outline_merge_source: 'history',
          version_label: 'v1.0.0',
          version_semver_valid: true,
        },
        { id: 'fac-1', name: '工厂预设', scope: 'factory' },
      ],
    });
    settingsMocks.fetchFactoryMergePresetPackages.mockResolvedValue({
      packages: [{ id: 'fac-1', name: '工厂预设', scope: 'factory' }],
    });
    settingsMocks.applyToposortMergePresetOrder.mockResolvedValue({ order: ['pkg-1'], edges: [], edge_count: 0 });
    settingsMocks.fetchMergePresetChangelog.mockResolvedValue({ package_id: 'pkg-1', entry_count: 1, entries: [{ index: 0 }] });
    settingsMocks.exportMergePresetPackages.mockResolvedValue({ packages: [] });
    settingsMocks.exportMergePreferences.mockResolvedValue({ scope: 'both' });
    settingsMocks.importMergePreferences.mockResolvedValue({});
    settingsMocks.importMergePresetPackages.mockResolvedValue({});
    settingsMocks.preflightMergePresetImport.mockResolvedValue({ blocked: false, would_import: 1, conflict_count: 0 });
    settingsMocks.previewMergePresetImportDiff.mockResolvedValue({ added: ['x'], updated: [], removed: [] });
    settingsMocks.applyToposortMergePresetOrder.mockResolvedValue({ reordered: 1 });
    settingsMocks.applyMergePresetConflictFix.mockResolvedValue({ conflict_count: 0 });
    settingsMocks.applyAllMergePresetConflictFixes.mockResolvedValue({ applied: 2, conflict_count: 0 });
    settingsMocks.publishMergePresetToFactory.mockResolvedValue({});
    settingsMocks.preflightFactoryMergePresetPull.mockResolvedValue({ conflict_count: 0 });
    settingsMocks.pullFactoryMergePresetsToProject.mockResolvedValue({ imported: 1, skipped: 0 });
    settingsMocks.fetchMergePresetChangelogDiff.mockResolvedValue({ change_count: 2, changes: [] });
    settingsMocks.restoreSettingsSnapshot.mockResolvedValue({
      pillars_text: '历史支柱',
      global_outline_text: '历史大纲',
      pillars_revision: 'hp',
      global_outline_revision: 'ho',
    });
    // T4a typed wrapper mock mirrors legacy restore response
    settingsMocks.restoreSettingsSnapshot.mockResolvedValue({
      pillars_text: '历史支柱',
      global_outline_text: '历史大纲',
      pillars_revision: 'hp',
      global_outline_revision: 'ho',
    });
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn(async () => undefined) },
    });
  });

  async function mountSettings() {
    const { useCreatorSettings } = await import('../../src/composables/useCreatorSettings.js');
    const error = ref<string | null>(null);
    const saveMessage = ref('');
    const conflictMessage = ref('');
    const globalOutlineText = ref('');
    const globalOutlineEditorRef = ref<HTMLElement | null>(null);
    const onAfterSettingsSave = vi.fn(async () => undefined);
    const handleSaveError = (err: unknown) => {
      error.value = err instanceof Error ? err.message : String(err);
    };
    const hub = useCreatorSettings({
      uiProfile: computed(() => ({})),
      overview: ref({}),
      error,
      saveMessage,
      conflictMessage,
      handleSaveError,
      onAfterSettingsSave,
      globalOutlineEditorRef,
      globalOutlineText,
      isWorkspaceColumnVisible: () => true,
      workspaceTabsEnabled: computed(() => true),
      logicCheckRunning: ref(false),
      logicCheckResult: ref(null),
      activeLogicCheckIssueIdx: ref(null),
      runCompanionLogicCheck: vi.fn(),
      handleLogicCheckIssueClick: vi.fn(),
      onLogicCheckIssueKeydown: vi.fn(),
    });
    return { hub, error, saveMessage, conflictMessage, globalOutlineText, globalOutlineEditorRef, onAfterSettingsSave, panel: hub.panelContext };
  }

  test('loadSettingsDocs hydrates baseline and clears diff', async () => {
    const { hub, panel } = await mountSettings();
    await hub.loadSettingsDocs();
    expect(panel.pillarsText.value).toBe('支柱A');
    expect(panel.globalOutlineText.value).toBe('大纲A');
    expect(panel.settingsHasUnsavedChanges.value).toBe(false);
  });

  test('requestSaveSettings short-circuits when unchanged', async () => {
    const { hub, panel, saveMessage } = await mountSettings();
    await hub.loadSettingsDocs();
    await panel.requestSaveSettings();
    expect(saveMessage.value).toBe('设定无变更');
  });

  test('requestSaveSettings opens three-way diff when history exists', async () => {
    const { hub, panel } = await mountSettings();
    await hub.loadSettingsDocs();
    await hub.loadSettingsHistory();
    panel.pillarsText.value = '支柱B';
    await panel.requestSaveSettings();
    expect(settingsMocks.previewSettingsThreeWay).toHaveBeenCalled();
    expect(panel.showSettingsDiff.value).toBe(true);
    expect(panel.settingsDiffSnippet.value.length).toBeGreaterThan(0);
    expect(panel.showMergeStrategy.value).toBe(true);
  });

  test('confirmSaveSettings persists docs and runs callback', async () => {
    const { hub, panel, onAfterSettingsSave } = await mountSettings();
    await hub.loadSettingsDocs();
    await hub.loadSettingsHistory();
    panel.pillarsText.value = '支柱B';
    await panel.requestSaveSettings();
    await panel.confirmSaveSettings();
    expect(settingsMocks.saveSettingsDocs).toHaveBeenCalled();
    expect(onAfterSettingsSave).toHaveBeenCalled();
    expect(panel.showSettingsDiff.value).toBe(false);
  });

  test('restoreSettingsHistory replaces editor text', async () => {
    const { hub, panel, saveMessage } = await mountSettings();
    await hub.loadSettingsDocs();
    await panel.restoreSettingsHistory('snap-1');
    expect(panel.pillarsText.value).toBe('历史支柱');
    expect(saveMessage.value).toContain('恢复');
  });

  test('merge preset helpers format and apply package', async () => {
    const { hub, panel } = await mountSettings();
    await hub.loadSettingsHistory();
    await hub.loadMergePresetPackages();
    expect(panel.formatMergePresetOption({ name: 'X', version_label: 'bad', version_semver_valid: false })).toContain('!');
    panel.selectedMergePresetPackage.value = 'pkg-1';
    await flushPromises();
    expect(panel.pillarsMergeSource.value).toBe('editor');
    panel.applyMergePreset('history');
    expect(panel.pillarsSnapshotId.value).toBe('snap-1');
  });

  test('export and import merge preset packages', async () => {
    const { hub, panel, saveMessage } = await mountSettings();
    await hub.loadMergePresetPackages();
    await panel.exportMergePresetPackages();
    expect(saveMessage.value).toContain('剪贴板');
    panel.importMergePresetPackagesJson.value = JSON.stringify({ packages: [] });
    await panel.preflightMergePresetImport();
    await panel.previewMergePresetImportDiff();
    await panel.importMergePresetPackagesFromJson();
    expect(settingsMocks.importMergePresetPackages).toHaveBeenCalled();
  });

  test('merge preset conflict fixes and toposort', async () => {
    const { hub, panel, saveMessage } = await mountSettings();
    await hub.loadMergePresetPackages();
    await panel.applyMergePresetConflictFix({ package_id: 'pkg-1', action: 'bump' });
    await panel.applyAllMergePresetConflictFixes();
    await panel.applyMergePresetToposort();
    expect(saveMessage.value).toContain('拓扑');
  });

  test('publish and pull factory merge presets', async () => {
    const { hub, panel, saveMessage } = await mountSettings();
    await hub.loadMergePresetPackages();
    panel.selectedMergePresetPackage.value = 'pkg-1';
    await flushPromises();
    await panel.publishMergePresetToFactory();
    expect(settingsMocks.publishMergePresetToFactory).toHaveBeenCalled();
    settingsMocks.preflightFactoryMergePresetPull.mockResolvedValueOnce({
      conflict_count: 1,
      conflicts: [{ package_id: 'fac-1' }],
    });
    await panel.pullFactoryMergePresets();
    expect(saveMessage.value).toContain('冲突');
    await panel.pullFactoryMergePresetsWithStrategy('fac-1', 'skip');
    expect(settingsMocks.pullFactoryMergePresetsToProject).toHaveBeenCalled();
  });

  test('merge preferences export import and changelog diff', async () => {
    const { hub, panel, saveMessage } = await mountSettings();
    await hub.loadSettingsHistory();
    await hub.loadMergePreferences();
    expect(panel.usesGlobalMergeDefault.value).toBe(true);
    await panel.exportMergePreferences();
    panel.importMergePrefsJson.value = JSON.stringify({ scope: 'both' });
    await panel.importMergePreferencesFromJson();
    expect(saveMessage.value).toContain('导入');
    panel.selectedMergePresetPackage.value = 'pkg-1';
    await panel.previewMergePresetChangelogDiff(0);
    expect(panel.mergePresetChangelogDiff.value.change_count).toBe(2);
  });

  test('cancelSettingsDiff and bindGlobalOutlineEditorRef', async () => {
    const { hub, panel, globalOutlineEditorRef } = await mountSettings();
    await hub.loadSettingsDocs();
    panel.showSettingsDiff.value = true;
    panel.cancelSettingsDiff();
    expect(panel.showSettingsDiff.value).toBe(false);
    const el = document.createElement('textarea');
    panel.bindGlobalOutlineEditorRef(el);
    expect(globalOutlineEditorRef.value).toBe(el);
  });

  test('loadMergePresetPackages clears state on API failure', async () => {
    settingsMocks.fetchMergePresetPackages.mockRejectedValueOnce(new Error('down'));
    const { hub, panel } = await mountSettings();
    await hub.loadMergePresetPackages();
    expect(panel.mergePresetPackages.value).toEqual([]);
  });

  test('requestSaveSettings uses two-way preview without history', async () => {
    settingsMocks.fetchSettingsHistory.mockResolvedValueOnce({ snapshots: [] });
    const { hub, panel } = await mountSettings();
    await hub.loadSettingsDocs();
    await hub.loadSettingsHistory();
    panel.pillarsText.value = '新支柱';
    await panel.requestSaveSettings();
    expect(settingsMocks.previewSettingsDocsDiff).toHaveBeenCalled();
  });

  test('importMergePresetPackagesFromJson stops when preflight blocked', async () => {
    settingsMocks.preflightMergePresetImport.mockResolvedValueOnce({
      blocked: true,
      would_import: 0,
      conflict_count: 2,
    });
    const { panel, saveMessage } = await mountSettings();
    panel.importMergePresetPackagesJson.value = JSON.stringify({ packages: [] });
    await panel.preflightMergePresetImport();
    await panel.importMergePresetPackagesFromJson();
    expect(settingsMocks.importMergePresetPackages).not.toHaveBeenCalled();
    expect(saveMessage.value).toContain('预检');
  });

  test('cancelSettingsDiff clears preview state', async () => {
    const { hub, panel } = await mountSettings();
    await hub.loadSettingsDocs();
    panel.pillarsText.value = '改动';
    await panel.requestSaveSettings();
    panel.cancelSettingsDiff();
    expect(panel.showSettingsDiff.value).toBe(false);
    expect(panel.settingsDiffPreview.value).toBeNull();
  });

  test('formatHistoryTime renders readable timestamp', async () => {
    const { panel } = await mountSettings();
    expect(panel.formatHistoryTime('2026-06-01T12:00:00Z')).toContain('2026');
  });
});
