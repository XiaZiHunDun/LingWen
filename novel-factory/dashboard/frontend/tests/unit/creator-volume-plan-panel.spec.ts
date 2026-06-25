// tests/unit/creator-volume-plan-panel.spec.ts — CreatorVolumePlanPanel 轻量挂载

import { describe, test, expect, vi } from 'vitest';
import { defineComponent, h, provide, ref } from 'vue';
import { mount } from '@vue/test-utils';
import CreatorVolumePlanPanel from '../../src/components/creator/CreatorVolumePlanPanel.vue';
import { CREATOR_VOLUME_PLAN_KEY, createCreatorVolumePlanContext } from '../../src/components/creator/creatorVolumePlanKey.js';
import { byTestid } from '../helpers/by-testid';

const childStubs = {
  CreatorVolumePlanTemplatesPanel: { template: '<div data-testid="stub-volume-templates" />' },
  CreatorVolumePlanDiffPanel: { template: '<div data-testid="stub-volume-diff" />' },
  CreatorVolumePlanMergeSplitPanel: { template: '<div data-testid="stub-volume-merge-split" />' },
};

function mountVolumePlanPanel(panelOverrides: Record<string, unknown> = {}) {
  const { editableVolumes: volumesSeed, ...restOverrides } = panelOverrides;
  const addVolume = vi.fn();
  const requestSaveVolumePlan = vi.fn();
  const panelContext = createCreatorVolumePlanContext({
    editableVolumes: ref((volumesSeed as object[] | undefined) ?? []),
    dragVolumeIndex: ref(null),
    saving: ref(false),
    addVolume,
    moveVolume: vi.fn(),
    toggleLock: vi.fn(),
    onVolumeDragStart: vi.fn(),
    onVolumeDrop: vi.fn(),
    requestSaveVolumePlan,
    ...restOverrides,
  });

  const Host = defineComponent({
    name: 'VolumePlanPanelHost',
    setup() {
      provide(CREATOR_VOLUME_PLAN_KEY, panelContext);
      return () => h(CreatorVolumePlanPanel);
    },
  });

  const wrapper = mount(Host, { global: { stubs: childStubs } });
  return { wrapper, panelContext, addVolume, requestSaveVolumePlan };
}

describe('CreatorVolumePlanPanel', () => {
  test('renders shell and child panel stubs', () => {
    const { wrapper } = mountVolumePlanPanel();
    expect(wrapper.find(byTestid('volume-plan-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('add-volume-btn')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-volume-templates')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-volume-diff')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-volume-merge-split')).exists()).toBe(true);
  });

  test('add-volume button delegates to injected addVolume', async () => {
    const { wrapper, addVolume } = mountVolumePlanPanel();
    await wrapper.find(byTestid('add-volume-btn')).trigger('click');
    expect(addVolume).toHaveBeenCalledTimes(1);
  });

  test('edit panel shows rows and save when volumes exist', () => {
    const { wrapper } = mountVolumePlanPanel({
      editableVolumes: [
        { label: '第一卷', start_chapter: 1, end_chapter: 10, core_conflict: '冲突', locked: false },
      ],
    });
    expect(wrapper.find(byTestid('volume-row-0')).exists()).toBe(true);
    expect(wrapper.find(byTestid('save-volume-plan-btn')).exists()).toBe(true);
  });

  test('save button delegates to requestSaveVolumePlan', async () => {
    const { wrapper, requestSaveVolumePlan } = mountVolumePlanPanel({
      editableVolumes: [
        { label: '第一卷', start_chapter: 1, end_chapter: 10, core_conflict: '', locked: false },
      ],
    });
    await wrapper.find(byTestid('save-volume-plan-btn')).trigger('click');
    expect(requestSaveVolumePlan).toHaveBeenCalledTimes(1);
  });
});
