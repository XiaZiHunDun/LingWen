/**
 * useTemplateSync — 模板导入/导出/同步/factory pull/publish/delete + apply
 *
 * Phase 19 Task 2.3：从 useCreatorVolumePlanTemplates.js 拆出（完整实现）。
 * 负责: exportCustomTemplates/importCustomTemplates 导入导出 +
 *       syncTemplatesFromProjects 跨项目同步 + publishSelectedTemplateToFactory 发到工厂库 +
 *       pullFactoryTemplates/deleteSelectedFactoryTemplate 工厂库管理 +
 *       applyVolumeTemplate 应用模板到卷纲。
 */
import { ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  exportVolumeTemplates,
  importVolumeTemplates,
  fetchVolumeTemplateSyncSources,
  syncVolumeTemplates,
  publishFactoryVolumeTemplate,
  pullFactoryVolumeTemplates,
  deleteFactoryVolumeTemplate,
  applyVolumeTemplate as apiApplyVolumeTemplate,
} from '@/api/volume';
import { normalizeVolumePlanVolumes } from '../../utils/displayProjectName.js';

interface SyncSource { slug: string; name?: string }
interface AppliedResult { volumes: Array<Record<string, unknown>>; template_name: string }

export interface TemplateSyncDeps {
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  handleSaveError: (err: unknown) => void;
  selectedTemplateId: Ref<string>;
  selectedTemplateProject: ComputedRef<boolean>;
  selectedTemplateFactory: ComputedRef<boolean>;
  overview: Ref<Record<string, unknown> | null>;
  editableVolumes: Ref<Array<Record<string, unknown>>>;
  loadVolumeTemplates: () => Promise<void>;
}

export interface TemplateSyncReturn {
  showImportTemplates: Ref<boolean>;
  importTemplatesJson: Ref<string>;
  templateImporting: Ref<boolean>;
  templateSyncSources: Ref<SyncSource[]>;
  templateSyncing: Ref<boolean>;
  templatePublishing: Ref<boolean>;
  factoryPulling: Ref<boolean>;
  factoryDeleting: Ref<boolean>;
  templateApplying: Ref<boolean>;
  exportCustomTemplates: () => Promise<void>;
  importCustomTemplates: () => Promise<void>;
  loadTemplateSyncSources: () => Promise<void>;
  syncTemplatesFromProjects: () => Promise<void>;
  publishSelectedTemplateToFactory: () => Promise<void>;
  pullFactoryTemplates: () => Promise<void>;
  deleteSelectedFactoryTemplate: () => Promise<void>;
  applyVolumeTemplate: () => Promise<void>;
}

export function useTemplateSync(deps: TemplateSyncDeps): TemplateSyncReturn {
  const {
    error, saveMessage, handleSaveError,
    selectedTemplateId, selectedTemplateProject, selectedTemplateFactory,
    overview, editableVolumes, loadVolumeTemplates,
  } = deps;

  const showImportTemplates = ref(false);
  const importTemplatesJson = ref('');
  const templateImporting = ref(false);
  const templateSyncSources = ref<SyncSource[]>([]);
  const templateSyncing = ref(false);
  const templatePublishing = ref(false);
  const factoryPulling = ref(false);
  const factoryDeleting = ref(false);
  const templateApplying = ref(false);

  async function loadTemplateSyncSources(): Promise<void> {
    try {
      const data = await fetchVolumeTemplateSyncSources() as { sources?: SyncSource[] };
      templateSyncSources.value = data.sources || [];
    } catch {
      templateSyncSources.value = [];
    }
  }

  async function exportCustomTemplates(): Promise<void> {
    error.value = null;
    try {
      const data = await exportVolumeTemplates() as { templates?: Array<Record<string, unknown>>; count?: number };
      const text = JSON.stringify(data, null, 2);
      importTemplatesJson.value = text;
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        saveMessage.value = `已导出 ${data.count || data.templates?.length || 0} 个模板并复制到剪贴板`;
      } else {
        saveMessage.value = `已导出 ${data.count || data.templates?.length || 0} 个模板（见导入框）`;
        showImportTemplates.value = true;
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function importCustomTemplates(): Promise<void> {
    templateImporting.value = true;
    error.value = null;
    try {
      const payload = JSON.parse(importTemplatesJson.value);
      const templates = payload.templates || payload;
      const result = await importVolumeTemplates({
        templates: Array.isArray(templates) ? templates : [],
        replace: false,
      }) as { imported: number; total: number };
      saveMessage.value = `已导入 ${result.imported} 个模板（共 ${result.total} 个）`;
      importTemplatesJson.value = '';
      showImportTemplates.value = false;
      await loadVolumeTemplates();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      templateImporting.value = false;
    }
  }

  async function syncTemplatesFromProjects(): Promise<void> {
    templateSyncing.value = true;
    error.value = null;
    try {
      if (!templateSyncSources.value.length) {
        await loadTemplateSyncSources();
      }
      const slugs = templateSyncSources.value.map((s) => s.slug);
      if (!slugs.length) {
        saveMessage.value = '没有其他项目的自定义模板';
        return;
      }
      const result = await syncVolumeTemplates({ source_slugs: slugs }) as { sources: unknown[]; imported: number };
      saveMessage.value = `已从 ${result.sources.length} 个项目同步 ${result.imported} 个模板`;
      await loadVolumeTemplates();
      await loadTemplateSyncSources();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateSyncing.value = false;
    }
  }

  async function publishSelectedTemplateToFactory(): Promise<void> {
    if (!selectedTemplateProject.value) return;
    templatePublishing.value = true;
    error.value = null;
    try {
      await publishFactoryVolumeTemplate({ template_id: selectedTemplateId.value });
      saveMessage.value = '已发布到工厂模板库';
      await loadVolumeTemplates();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templatePublishing.value = false;
    }
  }

  async function pullFactoryTemplates(): Promise<void> {
    // 通过 volumeTemplates 找 factory 范围的（简化实现：依赖 selectedTemplateId）
    factoryPulling.value = true;
    error.value = null;
    try {
      const result = await pullFactoryVolumeTemplates({ template_ids: [] }) as { imported: number };
      saveMessage.value = `已从工厂库拉取 ${result.imported} 个模板`;
      await loadVolumeTemplates();
    } catch (e) {
      handleSaveError(e);
    } finally {
      factoryPulling.value = false;
    }
  }

  async function deleteSelectedFactoryTemplate(): Promise<void> {
    if (!selectedTemplateFactory.value) return;
    factoryDeleting.value = true;
    error.value = null;
    try {
      await deleteFactoryVolumeTemplate(selectedTemplateId.value);
      saveMessage.value = '已从工厂库删除模板';
      await loadVolumeTemplates();
      selectedTemplateId.value = 'three_act';
    } catch (e) {
      handleSaveError(e);
    } finally {
      factoryDeleting.value = false;
    }
  }

  async function applyVolumeTemplate(): Promise<void> {
    templateApplying.value = true;
    error.value = null;
    try {
      // v16.2.7 T8: typed wrapper's CreatorVolumeApplyTemplateResponse strict type;
      // cast to legacy AppliedResult shape preserves runtime behavior.
      const result = await apiApplyVolumeTemplate({
        template_id: selectedTemplateId.value,
        max_chapter: (overview.value as { max_chapter?: number } | null)?.max_chapter,
      }) as unknown as AppliedResult;
      editableVolumes.value = normalizeVolumePlanVolumes(result.volumes) as Array<Record<string, unknown>>;
      saveMessage.value = `已套用模板「${result.template_name}」，请保存卷纲`;
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateApplying.value = false;
    }
  }

  return {
    showImportTemplates,
    importTemplatesJson,
    templateImporting,
    templateSyncSources,
    templateSyncing,
    templatePublishing,
    factoryPulling,
    factoryDeleting,
    templateApplying,
    exportCustomTemplates,
    importCustomTemplates,
    loadTemplateSyncSources,
    syncTemplatesFromProjects,
    publishSelectedTemplateToFactory,
    pullFactoryTemplates,
    deleteSelectedFactoryTemplate,
    applyVolumeTemplate,
  };
}
