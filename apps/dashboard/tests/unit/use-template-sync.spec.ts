/**
 * useTemplateSync 子模块独立测试
 *
 * Phase 42: 为 Phase 19.2 useTemplateSync 子模块添加专门测试。
 * 重点测试：导入/导出/同步/factory pull/publish/delete/apply。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

const syncMocks = vi.hoisted(() => ({
  exportCreatorVolumeTemplates: vi.fn(),
  importCreatorVolumeTemplates: vi.fn(),
  fetchCreatorVolumeTemplateSyncSources: vi.fn(),
  syncCreatorVolumeTemplates: vi.fn(),
  publishCreatorVolumeTemplateToFactory: vi.fn(),
  pullCreatorFactoryVolumeTemplates: vi.fn(),
  deleteCreatorFactoryVolumeTemplate: vi.fn(),
  applyCreatorVolumeTemplate: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => {
  const m = syncMocks;
  return {
    exportCreatorVolumeTemplates: (...args: unknown[]) => m.exportCreatorVolumeTemplates(...args),
    importCreatorVolumeTemplates: (...args: unknown[]) => m.importCreatorVolumeTemplates(...args),
    fetchCreatorVolumeTemplateSyncSources: (...args: unknown[]) => m.fetchCreatorVolumeTemplateSyncSources(...args),
    syncCreatorVolumeTemplates: (...args: unknown[]) => m.syncCreatorVolumeTemplates(...args),
    publishCreatorVolumeTemplateToFactory: (...args: unknown[]) => m.publishCreatorVolumeTemplateToFactory(...args),
    pullCreatorFactoryVolumeTemplates: (...args: unknown[]) => m.pullCreatorFactoryVolumeTemplates(...args),
    deleteCreatorFactoryVolumeTemplate: (...args: unknown[]) => m.deleteCreatorFactoryVolumeTemplate(...args),
    applyCreatorVolumeTemplate: (...args: unknown[]) => m.applyCreatorVolumeTemplate(...args),
  };
});

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
    syncMocks.exportCreatorVolumeTemplates.mockResolvedValueOnce({
      templates: [{ id: '1', name: 't1' }],
      count: 1,
    });
    const s = mountSync();
    await s.exportCustomTemplates();
    expect(s.importTemplatesJson.value).toContain('t1');
    expect(s.saveMessage.value).toContain('已导出');
  });

  it('exportCustomTemplates opens dialog when no clipboard', async () => {
    syncMocks.exportCreatorVolumeTemplates.mockResolvedValueOnce({
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
    syncMocks.importCreatorVolumeTemplates.mockResolvedValueOnce({
      imported: 2, total: 5,
    });
    const s = mountSync();
    s.importTemplatesJson.value = JSON.stringify({ templates: [{ id: '1' }, { id: '2' }] });
    await s.importCustomTemplates();
    expect(syncMocks.importCreatorVolumeTemplates).toHaveBeenCalled();
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
    syncMocks.fetchCreatorVolumeTemplateSyncSources.mockResolvedValueOnce({
      sources: [{ slug: 'p1', name: 'Project 1' }],
    });
    const s = mountSync();
    await s.loadTemplateSyncSources();
    expect(s.templateSyncSources.value).toHaveLength(1);
  });

  it('loadTemplateSyncSources sets empty on failure', async () => {
    syncMocks.fetchCreatorVolumeTemplateSyncSources.mockRejectedValueOnce(new Error('down'));
    const s = mountSync();
    await s.loadTemplateSyncSources();
    expect(s.templateSyncSources.value).toEqual([]);
  });

  it('syncTemplatesFromProjects fetches and saves message', async () => {
    syncMocks.fetchCreatorVolumeTemplateSyncSources.mockResolvedValueOnce({
      sources: [{ slug: 'p1' }, { slug: 'p2' }],
    });
    syncMocks.syncCreatorVolumeTemplates.mockResolvedValueOnce({
      sources: ['p1', 'p2'], imported: 3,
    });
    const s = mountSync();
    await s.syncTemplatesFromProjects();
    expect(s.saveMessage.value).toContain('已从 2 个项目');
    expect(s.saveMessage.value).toContain('3 个模板');
  });

  it('syncTemplatesFromProjects no-op when no sources', async () => {
    syncMocks.fetchCreatorVolumeTemplateSyncSources.mockResolvedValueOnce({ sources: [] });
    const s = mountSync();
    await s.syncTemplatesFromProjects();
    expect(s.saveMessage.value).toContain('没有其他项目');
  });

  it('publishSelectedTemplateToFactory no-op when selectedTemplateProject false', async () => {
    // selectedTemplateProject computed 在我们的 mountSync 中固定为 false
    const s = mountSync();
    await s.publishSelectedTemplateToFactory();
    expect(syncMocks.publishCreatorVolumeTemplateToFactory).not.toHaveBeenCalled();
  });

  it('publishSelectedTemplateToFactory posts via API', async () => {
    syncMocks.publishCreatorVolumeTemplateToFactory.mockResolvedValueOnce(undefined);
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
    expect(syncMocks.publishCreatorVolumeTemplateToFactory).toHaveBeenCalled();
    expect(saveMessage.value).toContain('已发布');
  });

  it('pullFactoryTemplates updates and reloads', async () => {
    syncMocks.pullCreatorFactoryVolumeTemplates.mockResolvedValueOnce({ imported: 2 });
    const s = mountSync();
    await s.pullFactoryTemplates();
    expect(s.saveMessage.value).toContain('已从工厂库拉取');
  });

  it('deleteSelectedFactoryTemplate no-op when not factory', async () => {
    const s = mountSync();
    s.selectedTemplateId.value = 'project-template';
    await s.deleteSelectedFactoryTemplate();
    expect(syncMocks.deleteCreatorFactoryVolumeTemplate).not.toHaveBeenCalled();
  });

  it('applyVolumeTemplate applies volumes to editable', async () => {
    syncMocks.applyCreatorVolumeTemplate.mockResolvedValueOnce({
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