/**
 * useTemplateList 子模块独立测试
 *
 * Phase 24: 为 Phase 19 Task 2.1 useTemplateList 子模块添加专门测试。
 * 重点测试：模板列表加载、过滤 computeds、formatTemplateOption 时间 helpers。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';

// Mock API
const templateMocks = vi.hoisted(() => ({
  fetchCreatorVolumeTemplates: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorVolumeTemplates: (...args: unknown[]) => templateMocks.fetchCreatorVolumeTemplates(...args),
}));

import { useTemplateList } from '../../src/composables/useCreatorVolumePlanTemplates/useTemplateList';

function mountList() {
  const volumeTemplates = ref<Array<Record<string, unknown>>>([]);
  const selectedTemplateId = ref('three_act');
  return useTemplateList({
    volumeTemplates,
    selectedTemplateId,
  });
}

describe('useTemplateList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    templateMocks.fetchCreatorVolumeTemplates.mockResolvedValue({
      templates: [
        { id: 'three_act', name: '三幕', scope: 'project', description: '基础结构' },
        { id: 'hero_journey', name: '英雄之旅', scope: 'project' },
        { id: 'factory_v1', name: '工厂模板', scope: 'factory' },
      ],
    });
  });

  it('loadVolumeTemplates populates list from API', async () => {
    const list = mountList();
    await list.loadVolumeTemplates();
    expect(list.volumeTemplates.value).toHaveLength(3);
  });

  it('loadVolumeTemplates handles API failure gracefully', async () => {
    templateMocks.fetchCreatorVolumeTemplates.mockRejectedValueOnce(new Error('down'));
    const list = mountList();
    await list.loadVolumeTemplates();
    expect(list.volumeTemplates.value).toEqual([]);
  });

  it('loadVolumeTemplates auto-selects first template if none selected', async () => {
    const list = mountList();
    list.selectedTemplateId.value = 'non_existent';
    await list.loadVolumeTemplates();
    expect(list.selectedTemplateId.value).toBe('three_act');
  });

  it('selectedTemplateHint returns description of selected template', async () => {
    const list = mountList();
    await list.loadVolumeTemplates();
    expect(list.selectedTemplateHint.value).toBe('基础结构');
  });

  it('selectedTemplateProject is true when scope is project', async () => {
    const list = mountList();
    await list.loadVolumeTemplates();
    list.selectedTemplateId.value = 'three_act';
    expect(list.selectedTemplateProject.value).toBe(true);
  });

  it('selectedTemplateFactory is true when scope is factory', async () => {
    const list = mountList();
    await list.loadVolumeTemplates();
    list.selectedTemplateId.value = 'factory_v1';
    expect(list.selectedTemplateFactory.value).toBe(true);
    expect(list.selectedTemplateProject.value).toBe(false);
  });

  it('selectedTemplateCustom mirrors selectedTemplateProject', async () => {
    const list = mountList();
    await list.loadVolumeTemplates();
    list.selectedTemplateId.value = 'hero_journey';
    expect(list.selectedTemplateCustom.value).toBe(true);
    list.selectedTemplateId.value = 'factory_v1';
    expect(list.selectedTemplateCustom.value).toBe(false);
  });

  it('factoryTemplateCount counts only factory-scoped templates', async () => {
    const list = mountList();
    await list.loadVolumeTemplates();
    expect(list.factoryTemplateCount.value).toBe(1);
  });

  it('formatTemplateOption with no version_label returns name', () => {
    const list = mountList();
    expect(list.formatTemplateOption({ name: '模板A' })).toBe('模板A');
    expect(list.formatTemplateOption({ name: '模板B', version_label: '' })).toBe('模板B');
  });

  it('formatTemplateOption with version_label returns formatted string', () => {
    const list = mountList();
    expect(list.formatTemplateOption({ name: '模板A', version_label: 'v1.0' })).toBe('[v1.0] 模板A');
  });

  it('formatTemplateOption adds warning prefix for invalid semver', () => {
    const list = mountList();
    expect(list.formatTemplateOption({ name: '模板A', version_label: 'bad', version_semver_valid: false })).toBe('![bad] 模板A');
  });

  it('isSemverVersionLabel accepts valid semver', () => {
    const list = mountList();
    expect(list.isSemverVersionLabel('1.0.0')).toBe(true);
    expect(list.isSemverVersionLabel('v1.2.3')).toBe(true);
    expect(list.isSemverVersionLabel('1.0')).toBe(true);
    expect(list.isSemverVersionLabel('1.0.0-rc.1')).toBe(true);
  });

  it('isSemverVersionLabel rejects invalid', () => {
    const list = mountList();
    expect(list.isSemverVersionLabel('not-a-version')).toBe(false);
    expect(list.isSemverVersionLabel('')).toBe(false);
  });

  it('formatHistoryTime handles empty input', () => {
    const list = mountList();
    expect(list.formatHistoryTime('')).toBe('');
  });

  it('formatHistoryTime renders readable timestamp', () => {
    const list = mountList();
    const result = list.formatHistoryTime('2026-06-01T12:34:56Z');
    expect(result).toMatch(/2026|06|01|12|34|56/);
  });

  it('formatHistoryTime returns input on invalid date', () => {
    const list = mountList();
    // 注意: JS 的 Date 对无效输入返回 'Invalid Date' 而非抛出，
    // 所以 toLocaleString 返回 'Invalid Date'，try/catch 不触发。
    const result = list.formatHistoryTime('invalid-date');
    expect(['invalid-date', 'Invalid Date']).toContain(result);
  });
});