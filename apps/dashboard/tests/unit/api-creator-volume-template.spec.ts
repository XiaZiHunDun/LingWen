/**
 * api/volumeTemplate 独立测试（Phase 62.5）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorVolumeTemplates,
  saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate,
  renameCreatorVolumeTemplate,
  setCreatorVolumeTemplateVersion,
  fetchCreatorVolumeTemplateChangelog,
  rollbackCreatorVolumeTemplate,
  importCreatorVolumeTemplates,
  exportCreatorVolumeTemplates,
  fetchCreatorVolumeTemplateSyncSources,
  syncCreatorVolumeTemplates,
  fetchCreatorFactoryVolumeTemplates,
  publishCreatorVolumeTemplateToFactory,
  pullCreatorFactoryVolumeTemplates,
  deleteCreatorFactoryVolumeTemplate,
} from '../../src/api/volumeTemplate.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/volumeTemplate', () => {
  it('fetchCreatorVolumeTemplates GETs /creator/volume-plan/templates', async () => {
    mocks.request.mockResolvedValueOnce({ templates: [] });
    await fetchCreatorVolumeTemplates();
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/templates');
  });

  it('saveCreatorVolumeTemplate POSTs body to /templates/save', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorVolumeTemplate({ name: 't1' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/templates/save', {
      method: 'POST',
      body: { name: 't1' },
    });
  });

  it('deleteCreatorVolumeTemplate DELETEs by encoded id', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await deleteCreatorVolumeTemplate('t/1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/t%2F1',
      { method: 'DELETE' },
    );
  });

  it('renameCreatorVolumeTemplate PATCHes encoded id', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await renameCreatorVolumeTemplate('t 1', { name: 'new' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/t%201',
      {
        method: 'PATCH',
        body: { name: 'new' },
      },
    );
  });

  it('setCreatorVolumeTemplateVersion PUTs version body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await setCreatorVolumeTemplateVersion('t1', { version: 2 });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/t1/version',
      {
        method: 'PUT',
        body: { version: 2 },
      },
    );
  });

  it('setCreatorVolumeTemplateVersion encodes id', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await setCreatorVolumeTemplateVersion('a/b', { version: 1 });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/a%2Fb/version',
      {
        method: 'PUT',
        body: { version: 1 },
      },
    );
  });

  it('fetchCreatorVolumeTemplateChangelog GETs /version-changelog', async () => {
    mocks.request.mockResolvedValueOnce({ changelog: [] });
    await fetchCreatorVolumeTemplateChangelog('t1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/t1/version-changelog',
    );
  });

  it('fetchCreatorVolumeTemplateChangelog encodes id', async () => {
    mocks.request.mockResolvedValueOnce({ changelog: [] });
    await fetchCreatorVolumeTemplateChangelog('t 1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/t%201/version-changelog',
    );
  });

  it('rollbackCreatorVolumeTemplate POSTs to /version-rollback', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await rollbackCreatorVolumeTemplate('t1', { version: 1 });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/t1/version-rollback',
      { method: 'POST', body: { version: 1 } },
    );
  });

  it('importCreatorVolumeTemplates POSTs body to /import', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await importCreatorVolumeTemplates({ data: 'x' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/templates/import', {
      method: 'POST',
      body: { data: 'x' },
    });
  });

  it('exportCreatorVolumeTemplates GETs /export', async () => {
    mocks.request.mockResolvedValueOnce({ data: 'x' });
    await exportCreatorVolumeTemplates();
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/templates/export');
  });

  it('fetchCreatorVolumeTemplateSyncSources GETs /sync-sources', async () => {
    mocks.request.mockResolvedValueOnce({ sources: [] });
    await fetchCreatorVolumeTemplateSyncSources();
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/templates/sync-sources');
  });

  it('syncCreatorVolumeTemplates POSTs body to /sync', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await syncCreatorVolumeTemplates({ source: 'github' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/templates/sync', {
      method: 'POST',
      body: { source: 'github' },
    });
  });

  it('fetchCreatorFactoryVolumeTemplates GETs /templates/factory', async () => {
    mocks.request.mockResolvedValueOnce({ templates: [] });
    await fetchCreatorFactoryVolumeTemplates();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/factory',
    );
  });

  it('publishCreatorVolumeTemplateToFactory POSTs body to /factory/publish', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await publishCreatorVolumeTemplateToFactory({ templateId: 't1' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/factory/publish',
      { method: 'POST', body: { templateId: 't1' } },
    );
  });

  it('pullCreatorFactoryVolumeTemplates POSTs body to /factory/pull', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await pullCreatorFactoryVolumeTemplates({ source: 'github' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/factory/pull',
      { method: 'POST', body: { source: 'github' } },
    );
  });

  it('deleteCreatorFactoryVolumeTemplate DELETEs encoded id', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await deleteCreatorFactoryVolumeTemplate('t/1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/factory/t%2F1',
      { method: 'DELETE' },
    );
  });
});
