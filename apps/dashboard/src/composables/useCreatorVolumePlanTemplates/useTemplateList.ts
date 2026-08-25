/**
 * useTemplateList — 模板列表 + 选择 + 视图 computeds
 *
 * Phase 19 Task 2：从 useCreatorVolumePlanTemplates.js 拆出（完整实现）。
 * 负责: volumeTemplates + selectedTemplateId + loadVolumeTemplates +
 *       selectedTemplateHint/Project/Factory/Custom/factoryTemplateCount computeds +
 *       formatTemplateOption/isSemverVersionLabel/formatHistoryTime helpers。
 */
import { computed, ref, watch } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { fetchCreatorVolumeTemplates } from '../../api/index.js';

interface TemplateRow {
  id?: string;
  name?: string;
  scope?: 'project' | 'factory';
  description?: string;
  version_label?: string;
  version_semver_valid?: boolean;
  version_changelog?: Array<Record<string, unknown>>;
}

export interface TemplateListDeps {
  volumeTemplates: Ref<TemplateRow[]>;
  selectedTemplateId: Ref<string>;
}

export interface TemplateListReturn {
  volumeTemplates: Ref<TemplateRow[]>;
  selectedTemplateId: Ref<string>;
  selectedTemplateHint: ComputedRef<string>;
  selectedTemplateProject: ComputedRef<boolean>;
  selectedTemplateFactory: ComputedRef<boolean>;
  selectedTemplateCustom: ComputedRef<boolean>;
  factoryTemplateCount: ComputedRef<number>;
  formatTemplateOption: (template: TemplateRow) => string;
  isSemverVersionLabel: (label: string) => boolean;
  formatHistoryTime: (iso: string) => string;
  loadVolumeTemplates: () => Promise<void>;
}

const VERSION_SEMVER_PATTERN = /^v?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9][a-zA-Z0-9.-]*)?$/i;

export function useTemplateList(deps: TemplateListDeps): TemplateListReturn {
  const { volumeTemplates, selectedTemplateId } = deps;

  async function loadVolumeTemplates(): Promise<void> {
    try {
      const data = await fetchCreatorVolumeTemplates() as { templates?: TemplateRow[] };
      volumeTemplates.value = data.templates || [];
      if (volumeTemplates.value.length && !volumeTemplates.value.some((t) => t.id === selectedTemplateId.value)) {
        const firstId = volumeTemplates.value[0].id || '';
        if (firstId) selectedTemplateId.value = firstId;
      }
    } catch {
      volumeTemplates.value = [];
    }
  }

  const selectedTemplateHint = computed<string>(() => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    return row?.description || '';
  });

  const selectedTemplateProject = computed<boolean>(() => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    return row?.scope === 'project';
  });

  const selectedTemplateFactory = computed<boolean>(() => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    return row?.scope === 'factory';
  });

  const selectedTemplateCustom = computed<boolean>(() => selectedTemplateProject.value);

  const factoryTemplateCount = computed<number>(() =>
    volumeTemplates.value.filter((t) => t.scope === 'factory').length,
  );

  function formatTemplateOption(template: TemplateRow): string {
    if (template.version_label) {
      const prefix = template.version_semver_valid === false ? '!' : '';
      return `${prefix}[${template.version_label}] ${template.name || ''}`;
    }
    return template.name || '';
  }

  function isSemverVersionLabel(label: string): boolean {
    return VERSION_SEMVER_PATTERN.test(String(label || '').trim());
  }

  function formatHistoryTime(iso: string): string {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleString('zh-CN', { hour12: false });
    } catch {
      return iso;
    }
  }

  // 监听 selectedTemplateId 变化（主 hook 仍可监听，保留 watch 占位）
  watch(selectedTemplateId, () => {
    // 由 useTemplateEditor 真正处理（version_label/changelog 加载等）
  });

  return {
    volumeTemplates,
    selectedTemplateId,
    selectedTemplateHint,
    selectedTemplateProject,
    selectedTemplateFactory,
    selectedTemplateCustom,
    factoryTemplateCount,
    formatTemplateOption,
    isSemverVersionLabel,
    formatHistoryTime,
    loadVolumeTemplates,
  };
}
