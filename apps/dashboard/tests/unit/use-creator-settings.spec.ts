// tests/unit/use-creator-settings.spec.ts — useCreatorSettings 编排

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, ref } from 'vue';
import { flushPromises } from '@vue/test-utils';

const settingsMocks = vi.hoisted(() => ({
  fetchCreatorSettingsDocs: vi.fn(),
  saveCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsThreeWay: vi.fn(),
  previewCreatorSettingsMerge: vi.fn(),
  fetchCreatorMergePreferences: vi.fn(),
  exportCreatorMergePreferences: vi.fn(),
  importCreatorMergePreferences: vi.fn(),
  fetchCreatorSettingsHistory: vi.fn(),
  restoreCreatorSettingsSnapshot: vi.fn(),
  preflightCreatorFactoryMergePresetPull: vi.fn(),
  fetchCreatorMergePresetChangelog: vi.fn(),
  fetchCreatorMergePresetChangelogDiff: vi.fn(),
  fetchCreatorMergePresetToposort: vi.fn(),
  fetchCreatorMergePresetPackages: vi.fn(),
  fetchCreatorFactoryMergePresetPackages: vi.fn(),
  fetchCreatorMergePresetGraph: vi.fn(),
  fetchCreatorMergePresetConflicts: vi.fn(),
  fetchCreatorMergePresetConflictFixes: vi.fn(),
  applyCreatorMergePresetConflictFix: vi.fn(),
  applyAllCreatorMergePresetConflictFixes: vi.fn(),
  preflightCreatorMergePresetImport: vi.fn(),
  previewCreatorMergePresetImportDiff: vi.fn(),
  applyCreatorMergePresetToposort: vi.fn(),
  exportCreatorMergePresetPackages: vi.fn(),
  importCreatorMergePresetPackages: vi.fn(),
  publishCreatorMergePresetToFactory: vi.fn(),
  pullCreatorFactoryMergePresetPackages: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorSettingsDocs: (...args: unknown[]) => settingsMocks.fetchCreatorSettingsDocs(...args),
  saveCreatorSettingsDocs: (...args: unknown[]) => settingsMocks.saveCreatorSettingsDocs(...args),
  previewCreatorSettingsDocs: (...args: unknown[]) => settingsMocks.previewCreatorSettingsDocs(...args),
  previewCreatorSettingsThreeWay: (...args: unknown[]) => settingsMocks.previewCreatorSettingsThreeWay(...args),
  previewCreatorSettingsMerge: (...args: unknown[]) => settingsMocks.previewCreatorSettingsMerge(...args),
  fetchCreatorMergePreferences: (...args: unknown[]) => settingsMocks.fetchCreatorMergePreferences(...args),
  exportCreatorMergePreferences: (...args: unknown[]) => settingsMocks.exportCreatorMergePreferences(...args),
  importCreatorMergePreferences: (...args: unknown[]) => settingsMocks.importCreatorMergePreferences(...args),
  fetchCreatorSettingsHistory: (...args: unknown[]) => settingsMocks.fetchCreatorSettingsHistory(...args),
  restoreCreatorSettingsSnapshot: (...args: unknown[]) => settingsMocks.restoreCreatorSettingsSnapshot(...args),
  preflightCreatorFactoryMergePresetPull: (...args: unknown[]) => settingsMocks.preflightCreatorFactoryMergePresetPull(...args),
  fetchCreatorMergePresetChangelog: (...args: unknown[]) => settingsMocks.fetchCreatorMergePresetChangelog(...args),
  fetchCreatorMergePresetChangelogDiff: (...args: unknown[]) => settingsMocks.fetchCreatorMergePresetChangelogDiff(...args),
  fetchCreatorMergePresetToposort: (...args: unknown[]) => settingsMocks.fetchCreatorMergePresetToposort(...args),
  fetchCreatorMergePresetPackages: (...args: unknown[]) => settingsMocks.fetchCreatorMergePresetPackages(...args),
  fetchCreatorFactoryMergePresetPackages: (...args: unknown[]) => settingsMocks.fetchCreatorFactoryMergePresetPackages(...args),
  fetchCreatorMergePresetGraph: (...args: unknown[]) => settingsMocks.fetchCreatorMergePresetGraph(...args),
  fetchCreatorMergePresetConflicts: (...args: unknown[]) => settingsMocks.fetchCreatorMergePresetConflicts(...args),
  fetchCreatorMergePresetConflictFixes: (...args: unknown[]) => settingsMocks.fetchCreatorMergePresetConflictFixes(...args),
  applyCreatorMergePresetConflictFix: (...args: unknown[]) => settingsMocks.applyCreatorMergePresetConflictFix(...args),
  applyAllCreatorMergePresetConflictFixes: (...args: unknown[]) => settingsMocks.applyAllCreatorMergePresetConflictFixes(...args),
  preflightCreatorMergePresetImport: (...args: unknown[]) => settingsMocks.preflightCreatorMergePresetImport(...args),
  previewCreatorMergePresetImportDiff: (...args: unknown[]) => settingsMocks.previewCreatorMergePresetImportDiff(...args),
  applyCreatorMergePresetToposort: (...args: unknown[]) => settingsMocks.applyCreatorMergePresetToposort(...args),
  exportCreatorMergePresetPackages: (...args: unknown[]) => settingsMocks.exportCreatorMergePresetPackages(...args),
  importCreatorMergePresetPackages: (...args: unknown[]) => settingsMocks.importCreatorMergePresetPackages(...args),
  publishCreatorMergePresetToFactory: (...args: unknown[]) => settingsMocks.publishCreatorMergePresetToFactory(...args),
  pullCreatorFactoryMergePresetPackages: (...args: unknown[]) => settingsMocks.pullCreatorFactoryMergePresetPackages(...args),
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
    settingsMocks.fetchCreatorMergePreferences.mockResolvedValue({
      pillars_merge_source: 'editor',
      global_outline_merge_source: 'history',
      merge_snapshot_id: 'snap-1',
      uses_global_default: true,
    });
    settingsMocks.fetchCreatorMergePresetPackages.mockResolvedValue({
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
    settingsMocks.fetchCreatorFactoryMergePresetPackages.mockResolvedValue({
      packages: [{ id: 'fac-1', name: '工厂预设', scope: 'factory' }],
    });
    settingsMocks.fetchCreatorMergePresetGraph.mockResolvedValue({ node_count: 1, edge_count: 0, nodes: [], edges: [] });
    settingsMocks.fetchCreatorMergePresetConflicts.mockResolvedValue({ conflict_count: 1, conflicts: [{ id: 'c1' }] });
    settingsMocks.fetchCreatorMergePresetConflictFixes.mockResolvedValue({ fix_count: 1, fixes: [{ package_id: 'pkg-1', action: 'bump' }] });
    settingsMocks.fetchCreatorMergePresetToposort.mockResolvedValue({ order: ['pkg-1'], edges: [], edge_count: 0 });
    settingsMocks.fetchCreatorMergePresetChangelog.mockResolvedValue({ package_id: 'pkg-1', entry_count: 1, entries: [{ index: 0 }] });
    settingsMocks.exportCreatorMergePresetPackages.mockResolvedValue({ packages: [] });
    settingsMocks.exportCreatorMergePreferences.mockResolvedValue({ scope: 'both' });
    settingsMocks.importCreatorMergePreferences.mockResolvedValue({});
    settingsMocks.importCreatorMergePresetPackages.mockResolvedValue({});
    settingsMocks.preflightCreatorMergePresetImport.mockResolvedValue({ blocked: false, would_import: 1, conflict_count: 0 });
    settingsMocks.previewCreatorMergePresetImportDiff.mockResolvedValue({ added: ['x'], updated: [], removed: [] });
    settingsMocks.applyCreatorMergePresetToposort.mockResolvedValue({ reordered: 1 });
    settingsMocks.applyCreatorMergePresetConflictFix.mockResolvedValue({ conflict_count: 0 });
    settingsMocks.applyAllCreatorMergePresetConflictFixes.mockResolvedValue({ applied: 2, conflict_count: 0 });
    settingsMocks.publishCreatorMergePresetToFactory.mockResolvedValue({});
    settingsMocks.preflightCreatorFactoryMergePresetPull.mockResolvedValue({ conflict_count: 0 });
    settingsMocks.pullCreatorFactoryMergePresetPackages.mockResolvedValue({ imported: 1, skipped: 0 });
    settingsMocks.fetchCreatorMergePresetChangelogDiff.mockResolvedValue({ change_count: 2, changes: [] });
    settingsMocks.restoreCreatorSettingsSnapshot.mockResolvedValue({
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
    expect(settingsMocks.previewCreatorSettingsThreeWay).toHaveBeenCalled();
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
    expect(settingsMocks.saveCreatorSettingsDocs).toHaveBeenCalled();
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
    expect(settingsMocks.importCreatorMergePresetPackages).toHaveBeenCalled();
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
    expect(settingsMocks.publishCreatorMergePresetToFactory).toHaveBeenCalled();
    settingsMocks.preflightCreatorFactoryMergePresetPull.mockResolvedValueOnce({
      conflict_count: 1,
      conflicts: [{ package_id: 'fac-1' }],
    });
    await panel.pullFactoryMergePresets();
    expect(saveMessage.value).toContain('冲突');
    await panel.pullFactoryMergePresetsWithStrategy('fac-1', 'skip');
    expect(settingsMocks.pullCreatorFactoryMergePresetPackages).toHaveBeenCalled();
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
    settingsMocks.fetchCreatorMergePresetPackages.mockRejectedValueOnce(new Error('down'));
    const { hub, panel } = await mountSettings();
    await hub.loadMergePresetPackages();
    expect(panel.mergePresetPackages.value).toEqual([]);
    expect(panel.mergePresetGraph.value.node_count).toBe(0);
  });

  test('requestSaveSettings uses two-way preview without history', async () => {
    settingsMocks.fetchCreatorSettingsHistory.mockResolvedValueOnce({ snapshots: [] });
    const { hub, panel } = await mountSettings();
    await hub.loadSettingsDocs();
    await hub.loadSettingsHistory();
    panel.pillarsText.value = '新支柱';
    await panel.requestSaveSettings();
    expect(settingsMocks.previewCreatorSettingsDocs).toHaveBeenCalled();
  });

  test('importMergePresetPackagesFromJson stops when preflight blocked', async () => {
    settingsMocks.preflightCreatorMergePresetImport.mockResolvedValueOnce({
      blocked: true,
      would_import: 0,
      conflict_count: 2,
    });
    const { panel, saveMessage } = await mountSettings();
    panel.importMergePresetPackagesJson.value = JSON.stringify({ packages: [] });
    await panel.preflightMergePresetImport();
    await panel.importMergePresetPackagesFromJson();
    expect(settingsMocks.importCreatorMergePresetPackages).not.toHaveBeenCalled();
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
