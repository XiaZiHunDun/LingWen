/**
 * api/mergePreset 独立测试（Phase 62.8）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  // MergePreset
  fetchCreatorMergePreferences,
  exportCreatorMergePreferences,
  importCreatorMergePreferences,
  fetchCreatorGlobalMergePreferences,
  fetchCreatorMergePresetPackages,
  exportCreatorMergePresetPackages,
  importCreatorMergePresetPackages,
  fetchCreatorFactoryMergePresetPackages,
  deleteCreatorFactoryMergePresetPackage,
  pullCreatorFactoryMergePresetPackages,
  publishCreatorMergePresetToFactory,
  preflightCreatorFactoryMergePresetPull,
  fetchCreatorFactoryMergePresetConflicts,
  resolveCreatorFactoryMergePresetConflict,
  preflightCreatorMergePresetImport,
  previewCreatorMergePresetImportDiff,
  fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePresetConflicts,
  fetchCreatorMergePresetConflictFixes,
  applyCreatorMergePresetConflictFix,
  applyAllCreatorMergePresetConflictFixes,
  fetchCreatorMergePresetGraph,
  fetchCreatorMergePresetToposort,
  applyCreatorMergePresetToposort,
  // SettingsDocs
  fetchCreatorSettingsDocs,
  saveCreatorSettingsDocs,
  previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge,
  fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot,
  // DiffCollab
  fetchCreatorDiffCollabNotes,
  saveCreatorDiffCollabNotes,
  // Wizard
  dismissCreatorWizardPanel,
  saveCreatorWizardPanelCollapsed,
  // Preferences
  fetchCreatorPreferences,
  saveCreatorPreferencesApi,
  fetchCreatorModels,
} from '../../src/api/mergePreset.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/mergePreset', () => {
  describe('mergePreset', () => {
    it('fetchCreatorMergePreferences GETs merge-preferences', async () => {
      mocks.request.mockResolvedValueOnce({ preferences: {} });
      await fetchCreatorMergePreferences();
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs/merge-preferences');
    });

    it('exportCreatorMergePreferences GETs merge-preferences/export', async () => {
      mocks.request.mockResolvedValueOnce({ blob: 'x' });
      await exportCreatorMergePreferences();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/export',
      );
    });

    it('importCreatorMergePreferences POSTs body to merge-preferences/import', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await importCreatorMergePreferences({ preferences: 'foo' });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/import',
        { method: 'POST', body: { preferences: 'foo' } },
      );
    });

    it('fetchCreatorGlobalMergePreferences GETs merge-preferences/global', async () => {
      mocks.request.mockResolvedValueOnce({ preferences: {} });
      await fetchCreatorGlobalMergePreferences();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/global',
      );
    });

    it('fetchCreatorMergePresetPackages GETs preset-packages', async () => {
      mocks.request.mockResolvedValueOnce({ packages: [] });
      await fetchCreatorMergePresetPackages();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages',
      );
    });

    it('exportCreatorMergePresetPackages GETs preset-packages/export', async () => {
      mocks.request.mockResolvedValueOnce({ blob: 'x' });
      await exportCreatorMergePresetPackages();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/export',
      );
    });

    it('importCreatorMergePresetPackages POSTs body to preset-packages/import', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await importCreatorMergePresetPackages({ packages: [] });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/import',
        { method: 'POST', body: { packages: [] } },
      );
    });

    it('fetchCreatorFactoryMergePresetPackages GETs preset-packages/factory', async () => {
      mocks.request.mockResolvedValueOnce({ packages: [] });
      await fetchCreatorFactoryMergePresetPackages();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/factory',
      );
    });

    it('deleteCreatorFactoryMergePresetPackage DELETEs encoded packageId', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await deleteCreatorFactoryMergePresetPackage('pkg/1');
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/factory/pkg%2F1',
        { method: 'DELETE' },
      );
    });

    it('pullCreatorFactoryMergePresetPackages POSTs body to factory/pull', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await pullCreatorFactoryMergePresetPackages({ ids: ['p1'] });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/factory/pull',
        { method: 'POST', body: { ids: ['p1'] } },
      );
    });

    it('publishCreatorMergePresetToFactory POSTs body to factory/publish', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await publishCreatorMergePresetToFactory({ packageId: 'p1' });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/factory/publish',
        { method: 'POST', body: { packageId: 'p1' } },
      );
    });

    it('preflightCreatorFactoryMergePresetPull POSTs body to factory/pull/preflight', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await preflightCreatorFactoryMergePresetPull({ ids: ['p1'] });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/factory/pull/preflight',
        { method: 'POST', body: { ids: ['p1'] } },
      );
    });

    it('fetchCreatorFactoryMergePresetConflicts GETs factory/conflicts', async () => {
      mocks.request.mockResolvedValueOnce({ conflicts: [] });
      await fetchCreatorFactoryMergePresetConflicts();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/factory/conflicts',
      );
    });

    it('resolveCreatorFactoryMergePresetConflict POSTs body to factory/merge-conflicts', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await resolveCreatorFactoryMergePresetConflict({ conflictId: 'c1', choice: 'ours' });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/factory/merge-conflicts',
        { method: 'POST', body: { conflictId: 'c1', choice: 'ours' } },
      );
    });

    it('preflightCreatorMergePresetImport POSTs body to import/preflight', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await preflightCreatorMergePresetImport({ payload: 'foo' });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/import/preflight',
        { method: 'POST', body: { payload: 'foo' } },
      );
    });

    it('previewCreatorMergePresetImportDiff POSTs body to import/preview-diff', async () => {
      mocks.request.mockResolvedValueOnce({ diff: {} });
      await previewCreatorMergePresetImportDiff({ payload: 'foo' });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/import/preview-diff',
        { method: 'POST', body: { payload: 'foo' } },
      );
    });

    it('fetchCreatorMergePresetChangelog GETs encoded packageId/.../changelog with limit', async () => {
      mocks.request.mockResolvedValueOnce({ changelog: [] });
      await fetchCreatorMergePresetChangelog('pkg/1', 25);
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/pkg%2F1/changelog?limit=25',
      );
    });

    it('fetchCreatorMergePresetChangelog defaults limit to 10', async () => {
      mocks.request.mockResolvedValueOnce({ changelog: [] });
      await fetchCreatorMergePresetChangelog('pkg1');
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/pkg1/changelog?limit=10',
      );
    });

    it('fetchCreatorMergePresetChangelogDiff GETs encoded packageId/.../changelog/diff with entry_index query', async () => {
      mocks.request.mockResolvedValueOnce({ diff: {} });
      await fetchCreatorMergePresetChangelogDiff('pkg/1', 5);
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/pkg%2F1/changelog/diff?entry_index=5',
      );
    });

    it('fetchCreatorMergePresetChangelogDiff defaults entryIndex to 0', async () => {
      mocks.request.mockResolvedValueOnce({ diff: {} });
      await fetchCreatorMergePresetChangelogDiff('pkg1');
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/pkg1/changelog/diff?entry_index=0',
      );
    });

    it('fetchCreatorMergePresetConflicts GETs preset-packages/conflicts', async () => {
      mocks.request.mockResolvedValueOnce({ conflicts: [] });
      await fetchCreatorMergePresetConflicts();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/conflicts',
      );
    });

    it('fetchCreatorMergePresetConflictFixes GETs preset-packages/conflicts/fixes', async () => {
      mocks.request.mockResolvedValueOnce({ fixes: [] });
      await fetchCreatorMergePresetConflictFixes();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/conflicts/fixes',
      );
    });

    it('applyCreatorMergePresetConflictFix POSTs body to conflicts/apply-fix', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await applyCreatorMergePresetConflictFix({ fixId: 'f1' });
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-fix',
        { method: 'POST', body: { fixId: 'f1' } },
      );
    });

    it('applyAllCreatorMergePresetConflictFixes POSTs without body to conflicts/apply-all', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await applyAllCreatorMergePresetConflictFixes();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-all',
        { method: 'POST' },
      );
    });

    it('fetchCreatorMergePresetGraph GETs preset-packages/graph', async () => {
      mocks.request.mockResolvedValueOnce({ graph: {} });
      await fetchCreatorMergePresetGraph();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/graph',
      );
    });

    it('fetchCreatorMergePresetToposort GETs preset-packages/toposort', async () => {
      mocks.request.mockResolvedValueOnce({ order: [] });
      await fetchCreatorMergePresetToposort();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/toposort',
      );
    });

    it('applyCreatorMergePresetToposort POSTs without body to toposort/apply', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await applyCreatorMergePresetToposort();
      expect(mocks.request).toHaveBeenCalledWith(
        '/creator/settings-docs/merge-preferences/preset-packages/toposort/apply',
        { method: 'POST' },
      );
    });
  });

  describe('settingsDocs', () => {
    it('fetchCreatorSettingsDocs GETs settings-docs', async () => {
      mocks.request.mockResolvedValueOnce({ docs: {} });
      await fetchCreatorSettingsDocs();
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs');
    });

    it('saveCreatorSettingsDocs PUTs body to settings-docs', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await saveCreatorSettingsDocs({ content: 'foo' });
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs', {
        method: 'PUT',
        body: { content: 'foo' },
      });
    });

    it('previewCreatorSettingsDocs POSTs body to settings-docs/preview', async () => {
      mocks.request.mockResolvedValueOnce({ preview: {} });
      await previewCreatorSettingsDocs({ content: 'foo' });
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs/preview', {
        method: 'POST',
        body: { content: 'foo' },
      });
    });

    it('previewCreatorSettingsThreeWay POSTs body to three-way-preview', async () => {
      mocks.request.mockResolvedValueOnce({ diff: {} });
      await previewCreatorSettingsThreeWay({ base: 'b', ours: 'o', theirs: 't' });
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs/three-way-preview', {
        method: 'POST',
        body: { base: 'b', ours: 'o', theirs: 't' },
      });
    });

    it('previewCreatorSettingsMerge POSTs body to merge-preview', async () => {
      mocks.request.mockResolvedValueOnce({ merged: {} });
      await previewCreatorSettingsMerge({ ours: 'o', theirs: 't' });
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs/merge-preview', {
        method: 'POST',
        body: { ours: 'o', theirs: 't' },
      });
    });

    it('fetchCreatorSettingsHistory GETs settings-docs/history', async () => {
      mocks.request.mockResolvedValueOnce({ history: [] });
      await fetchCreatorSettingsHistory();
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs/history');
    });

    it('restoreCreatorSettingsSnapshot POSTs body with snapshot_id to settings-docs/restore', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await restoreCreatorSettingsSnapshot('snap-42');
      expect(mocks.request).toHaveBeenCalledWith('/creator/settings-docs/restore', {
        method: 'POST',
        body: { snapshot_id: 'snap-42' },
      });
    });
  });

  describe('diffCollab', () => {
    it('fetchCreatorDiffCollabNotes GETs diff-collab-notes', async () => {
      mocks.request.mockResolvedValueOnce({ notes: [] });
      await fetchCreatorDiffCollabNotes();
      expect(mocks.request).toHaveBeenCalledWith('/creator/diff-collab-notes');
    });

    it('saveCreatorDiffCollabNotes PUTs body to diff-collab-notes', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await saveCreatorDiffCollabNotes({ notes: 'foo' });
      expect(mocks.request).toHaveBeenCalledWith('/creator/diff-collab-notes', {
        method: 'PUT',
        body: { notes: 'foo' },
      });
    });
  });

  describe('wizard', () => {
    it('dismissCreatorWizardPanel PUTs without body to onboarding/wizard-dismiss', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await dismissCreatorWizardPanel();
      expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/wizard-dismiss', {
        method: 'PUT',
      });
    });

    it('saveCreatorWizardPanelCollapsed PUTs body with collapsed to onboarding/wizard-collapse', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await saveCreatorWizardPanelCollapsed(true);
      expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/wizard-collapse', {
        method: 'PUT',
        body: { collapsed: true },
      });
    });

    it('saveCreatorWizardPanelCollapsed accepts false value', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await saveCreatorWizardPanelCollapsed(false);
      expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/wizard-collapse', {
        method: 'PUT',
        body: { collapsed: false },
      });
    });
  });

  describe('preferences', () => {
    it('fetchCreatorPreferences GETs preferences', async () => {
      mocks.request.mockResolvedValueOnce({ preferences: {} });
      await fetchCreatorPreferences();
      expect(mocks.request).toHaveBeenCalledWith('/creator/preferences');
    });

    it('saveCreatorPreferencesApi PUTs body to preferences', async () => {
      mocks.request.mockResolvedValueOnce({ ok: true });
      await saveCreatorPreferencesApi({ theme: 'dark' });
      expect(mocks.request).toHaveBeenCalledWith('/creator/preferences', {
        method: 'PUT',
        body: { theme: 'dark' },
      });
    });

    it('fetchCreatorModels GETs models', async () => {
      mocks.request.mockResolvedValueOnce({ models: [] });
      await fetchCreatorModels();
      expect(mocks.request).toHaveBeenCalledWith('/creator/models');
    });
  });
});
