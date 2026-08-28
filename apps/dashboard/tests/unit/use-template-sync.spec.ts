/**
 * useTemplateSync 子模块独立测试
 *
 * Phase 42: 为 Phase 19.2 useTemplateSync 子模块添加专门测试。
 * 重点测试：导入/导出/同步/factory pull/publish/delete/apply。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

const syncMocks = vi.hoisted(() => ({
  exportVolumeTemplates: vi.fn(),
  importVolumeTemplates: vi.fn(),
  fetchVolumeTemplateSyncSources: vi.fn(),
  syncVolumeTemplates: vi.fn(),
  publishFactoryVolumeTemplate: vi.fn(),
  pullFactoryVolumeTemplates: vi.fn(),
  deleteFactoryVolumeTemplate: vi.fn(),
  applyVolumeTemplate: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => {
  const m = syncMocks;
  return {
    exportVolumeTemplates: (...args: unknown[]) => m.exportVolumeTemplates(...args),
    importVolumeTemplates: (...args: unknown[]) => m.importVolumeTemplates(...args),
    fetchVolumeTemplateSyncSources: (...args: unknown[]) => m.fetchVolumeTemplateSyncSources(...args),
    syncVolumeTemplates: (...args: unknown[]) => m.syncVolumeTemplates(...args),
    publishFactoryVolumeTemplate: (...args: unknown[]) => m.publishFactoryVolumeTemplate(...args),
    pullFactoryVolumeTemplates: (...args: unknown[]) => m.pullFactoryVolumeTemplates(...args),
    deleteFactoryVolumeTemplate: (...args: unknown[]) => m.deleteFactoryVolumeTemplate(...args),
    applyVolumeTemplate: (...args: unknown[]) => m.applyVolumeTemplate(...args),
  };
});


// v16.2.7 T6.B: also mock the typed wrapper module. Per v16.2.5 §5.1 lesson 3.
vi.mock('../../src/api/volume', () => ({
  listVolumeTemplates: (...args: unknown[]) => syncMocks.listVolumeTemplates(...args),
  exportVolumeTemplates: (...args: unknown[]) => syncMocks.exportVolumeTemplates(...args),
  importVolumeTemplates: (...args: unknown[]) => syncMocks.importVolumeTemplates(...args),
  fetchVolumeTemplateSyncSources: (...args: unknown[]) => syncMocks.fetchVolumeTemplateSyncSources(...args),
  syncVolumeTemplates: (...args: unknown[]) => syncMocks.syncVolumeTemplates(...args),
  publishFactoryVolumeTemplate: (...args: unknown[]) => syncMocks.publishFactoryVolumeTemplate(...args),
  pullFactoryVolumeTemplates: (...args: unknown[]) => syncMocks.pullFactoryVolumeTemplates(...args),
  deleteFactoryVolumeTemplate: (...args: unknown[]) => syncMocks.deleteFactoryVolumeTemplate(...args),
  applyVolumeTemplate: (...args: unknown[]) => syncMocks.applyVolumeTemplate(...args),
}));

import { useTemplateSync } from '../../src/composables/useCreatorVolumePlanTemplates/useTemplateSync';

function mountSync() {
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const handleSaveError = vi.fn();
  const selectedTemplateId = ref('three_act');
  const overview = ref<Record<string, unknown> | null>(null);
  const editableVolumes = ref<Array<Record<string, unknown>>>([]);
  const loadVolumeTemplates = vi.fn(async () => {});
  const selectedTemplateProject = computed(() => false);
  const selectedTemplateFactory = computed(() => false);

  const ctx = useTemplateSync({
    error, saveMessage, handleSaveError,
    selectedTemplateId, selectedTemplateProject, selectedTemplateFactory,
    overview, editableVolumes, loadVolumeTemplates,
  } as unknown as Parameters<typeof useTemplateSync>[0]);
  return {
    ...ctx,
    error, saveMessage, handleSaveError, editableVolumes, selectedTemplateId,
    overview, loadVolumeTemplates,
  };
}

describe('useTemplateSync', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn(async () => undefined) },
    });
  });

  it('initial state has closed dialog', () => {
    const s = mountSync();
    expect(s.showImportTemplates.value).toBe(false);
    expect(s.importTemplatesJson.value).toBe('');
    expect(s.templateSyncSources.value).toEqual([]);
  });

  it('exportCustomTemplates populates importTemplatesJson', async () => {
    syncMocks.exportVolumeTemplates.mockResolvedValueOnce({
      templates: [{ id: '1', name: 't1' }],
      count: 1,
    });
    const s = mountSync();
    await s.exportCustomTemplates();
    expect(s.importTemplatesJson.value).toContain('t1');
    expect(s.saveMessage.value).toContain('已导出');
  });

  it('exportCustomTemplates opens dialog when no clipboard', async () => {
    syncMocks.exportVolumeTemplates.mockResolvedValueOnce({
      templates: [{ id: '1', name: 't1' }],
      count: 1,
    });
    // 临时移除 clipboard
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
    const s = mountSync();
    await s.exportCustomTemplates();
    expect(s.showImportTemplates.value).toBe(true);
  });

  it('importCustomTemplates parses JSON and posts', async () => {
    syncMocks.importVolumeTemplates.mockResolvedValueOnce({
      imported: 2, total: 5,
    });
    const s = mountSync();
    s.importTemplatesJson.value = JSON.stringify({ templates: [{ id: '1' }, { id: '2' }] });
    await s.importCustomTemplates();
    expect(syncMocks.importVolumeTemplates).toHaveBeenCalled();
    expect(s.saveMessage.value).toContain('已导入');
    expect(s.loadVolumeTemplates).toHaveBeenCalled();
  });

  it('importCustomTemplates handles parse failure', async () => {
    const s = mountSync();
    s.importTemplatesJson.value = '{invalid';
    await s.importCustomTemplates();
    expect(s.error.value).toBeTruthy();
  });

  it('loadTemplateSyncSources populates from API', async () => {
    syncMocks.fetchVolumeTemplateSyncSources.mockResolvedValueOnce({
      sources: [{ slug: 'p1', name: 'Project 1' }],
    });
    const s = mountSync();
    await s.loadTemplateSyncSources();
    expect(s.templateSyncSources.value).toHaveLength(1);
  });

  it('loadTemplateSyncSources sets empty on failure', async () => {
    syncMocks.fetchVolumeTemplateSyncSources.mockRejectedValueOnce(new Error('down'));
    const s = mountSync();
    await s.loadTemplateSyncSources();
    expect(s.templateSyncSources.value).toEqual([]);
  });

  it('syncTemplatesFromProjects fetches and saves message', async () => {
    syncMocks.fetchVolumeTemplateSyncSources.mockResolvedValueOnce({
      sources: [{ slug: 'p1' }, { slug: 'p2' }],
    });
    syncMocks.syncVolumeTemplates.mockResolvedValueOnce({
      sources: ['p1', 'p2'], imported: 3,
    });
    const s = mountSync();
    await s.syncTemplatesFromProjects();
    expect(s.saveMessage.value).toContain('已从 2 个项目');
    expect(s.saveMessage.value).toContain('3 个模板');
  });

  it('syncTemplatesFromProjects no-op when no sources', async () => {
    syncMocks.fetchVolumeTemplateSyncSources.mockResolvedValueOnce({ sources: [] });
    const s = mountSync();
    await s.syncTemplatesFromProjects();
    expect(s.saveMessage.value).toContain('没有其他项目');
  });

  it('publishSelectedTemplateToFactory no-op when selectedTemplateProject false', async () => {
    // selectedTemplateProject computed 在我们的 mountSync 中固定为 false
    const s = mountSync();
    await s.publishSelectedTemplateToFactory();
    expect(syncMocks.publishFactoryVolumeTemplate).not.toHaveBeenCalled();
  });

  it('publishSelectedTemplateToFactory posts via API', async () => {
    syncMocks.publishFactoryVolumeTemplate.mockResolvedValueOnce(undefined);
    // 替换 selectedTemplateProject 为 true 的 mount
    const overview = ref<Record<string, unknown> | null>(null);
    const editableVolumes = ref<Array<Record<string, unknown>>>([]);
    const error = ref<string | null>(null);
    const saveMessage = ref('');
    const handleSaveError = vi.fn();
    const loadVolumeTemplates = vi.fn(async () => {});
    const selectedTemplateId = ref('p-1');
    const selectedTemplateProject = computed(() => true);
    const selectedTemplateFactory = computed(() => false);

    const ctx = useTemplateSync({
      error, saveMessage, handleSaveError,
      selectedTemplateId, selectedTemplateProject, selectedTemplateFactory,
      overview, editableVolumes, loadVolumeTemplates,
    } as unknown as Parameters<typeof useTemplateSync>[0]);
    await ctx.publishSelectedTemplateToFactory();
    expect(syncMocks.publishFactoryVolumeTemplate).toHaveBeenCalled();
    expect(saveMessage.value).toContain('已发布');
  });

  it('pullFactoryTemplates updates and reloads', async () => {
    syncMocks.pullFactoryVolumeTemplates.mockResolvedValueOnce({ imported: 2 });
    const s = mountSync();
    await s.pullFactoryTemplates();
    expect(s.saveMessage.value).toContain('已从工厂库拉取');
  });

  it('deleteSelectedFactoryTemplate no-op when not factory', async () => {
    const s = mountSync();
    s.selectedTemplateId.value = 'project-template';
    await s.deleteSelectedFactoryTemplate();
    expect(syncMocks.deleteFactoryVolumeTemplate).not.toHaveBeenCalled();
  });

  it('applyVolumeTemplate applies volumes to editable', async () => {
    syncMocks.applyVolumeTemplate.mockResolvedValueOnce({
      volumes: [{ label: '新卷', start_chapter: 1, end_chapter: 5 }],
      template_name: '新模板',
    });
    const s = mountSync();
    s.overview.value = { max_chapter: 10 };
    await s.applyVolumeTemplate();
    expect(s.editableVolumes.value).toHaveLength(1);
    expect(s.saveMessage.value).toContain('新模板');
  });
});
