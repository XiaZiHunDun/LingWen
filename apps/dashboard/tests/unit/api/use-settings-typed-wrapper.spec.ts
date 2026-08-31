/**
 * Phase 126 v16.2.2 Task 6 (T3) URL contract regression test for settings.ts
 * typed wrapper.
 *
 * Goal: lock the URL contract to `/creator/settings-docs*` (relative to
 * BASE_URL='/api') so the /api/api/ URL duplication bug cannot regress
 * (v16.2.1 carried it into world.ts/workspace.ts/quality.ts; carryover to
 * v16.2.7. This wrapper is being authored AFTER the fix so it must NOT
 * regress).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as settingsApi from '@/api/settings';

describe('settings typed wrapper (v16.2.2 Task 6 / T3)', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({}),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // --- exports count: ≥15 wrappers per T3 spec ---

  it('exports ≥15 wrapper functions', () => {
    const wrappers = Object.entries(settingsApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBeGreaterThanOrEqual(15);
  });

  // --- static: no /api/ prefix in any wrapper body (TYPE-level regression lock) ---

  it('no wrapper body hardcodes /api/ prefix', () => {
    const wrappers = Object.entries(settingsApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      // The wrapper should call `request('/creator/...')`, never `request('/api/...')`
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/creator/);
      expect(src, `${name} should not contain 'fetch(' direct`).not.toMatch(/\bfetch\(/);
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('fetchSettingsDocs GETs /api/creator/settings-docs (no /api/api duplication)', async () => {
    await settingsApi.fetchSettingsDocs();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs');
  });

  it('saveSettingsDocs PUTs /api/creator/settings-docs', async () => {
    await settingsApi.saveSettingsDocs({ pillars_text: 'x', global_outline_text: 'y' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/settings-docs');
    expect(init.method).toBe('PUT');
  });

  it('previewSettingsDocsDiff POSTs /api/creator/settings-docs/preview', async () => {
    await settingsApi.previewSettingsDocsDiff({ pillars_text: 'x', global_outline_text: 'y' });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/preview');
  });

  it('previewSettingsThreeWay POSTs /api/creator/settings-docs/three-way-preview', async () => {
    await settingsApi.previewSettingsThreeWay({ pillars_text: 'x', global_outline_text: 'y' });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/three-way-preview');
  });

  it('previewSettingsMergeStrategy POSTs /api/creator/settings-docs/merge-preview', async () => {
    await settingsApi.previewSettingsMergeStrategy({ pillars_text: 'x', global_outline_text: 'y' });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preview');
  });

  it('fetchSettingsHistory GETs /api/creator/settings-docs/history', async () => {
    await settingsApi.fetchSettingsHistory();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/history');
  });

  it('restoreSettingsSnapshot POSTs /api/creator/settings-docs/restore', async () => {
    await settingsApi.restoreSettingsSnapshot({ snapshot_id: 's1' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/settings-docs/restore');
    expect(init.method).toBe('POST');
  });

  it('fetchMergePreferences GETs /api/creator/settings-docs/merge-preferences', async () => {
    await settingsApi.fetchMergePreferences();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences');
  });

  it('fetchGlobalMergePreferences GETs .../merge-preferences/global', async () => {
    await settingsApi.fetchGlobalMergePreferences();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences/global');
  });

  it('exportMergePreferences GETs .../merge-preferences/export', async () => {
    await settingsApi.exportMergePreferences();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences/export');
  });

  it('importMergePreferences POSTs .../merge-preferences/import', async () => {
    await settingsApi.importMergePreferences({ scope: 'project', project: {} });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences/import');
    expect(init.method).toBe('POST');
  });

  it('listMergePresetPackages GETs .../preset-packages', async () => {
    await settingsApi.listMergePresetPackages();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences/preset-packages');
  });

  it('listFactoryMergePresetPackages GETs .../preset-packages/factory', async () => {
    await settingsApi.listFactoryMergePresetPackages();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences/preset-packages/factory');
  });

  it('buildMergePresetGraph GETs .../preset-packages/graph', async () => {
    await settingsApi.buildMergePresetGraph();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences/preset-packages/graph');
  });

  it('detectMergePresetConflicts GETs .../preset-packages/conflicts', async () => {
    await settingsApi.detectMergePresetConflicts();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/settings-docs/merge-preferences/preset-packages/conflicts');
  });

  it('suggestMergePresetFixes GETs .../preset-packages/conflicts/fixes', async () => {
    await settingsApi.suggestMergePresetFixes();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/fixes',
    );
  });

  it('applyMergePresetConflictFix POSTs .../preset-packages/conflicts/apply-fix', async () => {
    await settingsApi.applyMergePresetConflictFix({
      package_id: 'pkg-1',
      action: 'bump_version',
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-fix',
    );
    expect(init.method).toBe('POST');
  });

  it('applyAllMergePresetConflictFixes POSTs .../preset-packages/conflicts/apply-all', async () => {
    await settingsApi.applyAllMergePresetConflictFixes();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-all',
    );
    expect(init.method).toBe('POST');
  });

  it('toposortMergePresetPackages GETs .../preset-packages/toposort', async () => {
    await settingsApi.toposortMergePresetPackages();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/toposort',
    );
  });

  it('applyToposortMergePresetOrder POSTs .../preset-packages/toposort/apply', async () => {
    await settingsApi.applyToposortMergePresetOrder();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/toposort/apply',
    );
    expect(init.method).toBe('POST');
  });

  it('previewMergePresetImportDiff POSTs .../preset-packages/import/preview-diff', async () => {
    await settingsApi.previewMergePresetImportDiff({ packages: [] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/import/preview-diff',
    );
    expect(init.method).toBe('POST');
  });

  it('preflightMergePresetImport POSTs .../preset-packages/import/preflight', async () => {
    await settingsApi.preflightMergePresetImport({ packages: [] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/import/preflight',
    );
    expect(init.method).toBe('POST');
  });

  it('exportMergePresetPackages GETs .../preset-packages/export', async () => {
    await settingsApi.exportMergePresetPackages();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/export',
    );
  });

  it('importMergePresetPackages POSTs .../preset-packages/import', async () => {
    await settingsApi.importMergePresetPackages({ packages: [] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/import',
    );
    expect(init.method).toBe('POST');
  });

  it('detectFactoryMergePresetConflicts GETs .../preset-packages/factory/conflicts', async () => {
    await settingsApi.detectFactoryMergePresetConflicts();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/factory/conflicts',
    );
  });

  it('resolveFactoryMergePresetConflict POSTs .../preset-packages/factory/merge-conflicts', async () => {
    await settingsApi.resolveFactoryMergePresetConflict({ package_id: 'pkg-1' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/factory/merge-conflicts',
    );
    expect(init.method).toBe('POST');
  });

  it('preflightFactoryMergePresetPull POSTs .../preset-packages/factory/pull/preflight', async () => {
    await settingsApi.preflightFactoryMergePresetPull({ package_ids: ['p1'] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/factory/pull/preflight',
    );
    expect(init.method).toBe('POST');
  });

  it('pullFactoryMergePresetsToProject POSTs .../preset-packages/factory/pull', async () => {
    await settingsApi.pullFactoryMergePresetsToProject({ package_ids: ['p1'] });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/factory/pull',
    );
    expect(init.method).toBe('POST');
  });

  it('deleteFactoryMergePresetPackage DELETEs .../preset-packages/factory/{id}', async () => {
    await settingsApi.deleteFactoryMergePresetPackage('pkg-1');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/factory/pkg-1',
    );
    expect(init.method).toBe('DELETE');
  });

  it('fetchMergePresetChangelog GETs .../preset-packages/{id}/changelog?limit=N', async () => {
    await settingsApi.fetchMergePresetChangelog('pkg-1', 20);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/pkg-1/changelog?limit=20',
    );
  });

  it('fetchMergePresetChangelogDiff GETs .../preset-packages/{id}/changelog/diff', async () => {
    await settingsApi.fetchMergePresetChangelogDiff('pkg-1', 3);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(
      '/api/creator/settings-docs/merge-preferences/preset-packages/pkg-1/changelog/diff?entry_index=3',
    );
  });
});
