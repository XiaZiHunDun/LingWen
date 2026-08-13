// tests/unit/creator-page-layout.spec.ts — CreatorPageLayout 轻量挂载

import { describe, test, expect, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorPageLayout from '../../src/components/creator/CreatorPageLayout.vue';
import { byTestid } from '../helpers/by-testid';

const useCreatorPage = vi.hoisted(() => vi.fn());

vi.mock('../../src/composables/index.js', () => ({
  useCreatorPage,
}));

const layoutStubs = {
  CreatorPageHeader: { template: '<div data-testid="stub-creator-header" />' },
  CreatorPageBanners: { template: '<div data-testid="stub-creator-banners" />' },
  CreatorInterventionBanner: { template: '<div data-testid="stub-intervention-banner" />' },
  CreatorWorkspaceShell: { template: '<div data-testid="stub-creator-workspace"><slot /></div>' },
  CreatorWritePanel: { template: '<div data-testid="stub-write-panel" />' },
  CreatorPulsePanel: { template: '<div data-testid="stub-pulse-panel" />' },
  CreatorMemoryPanel: { template: '<div data-testid="stub-memory-panel" />' },
  CreatorVolumePlanShareModals: { template: '<div data-testid="stub-volume-share-modals" />' },
  CreatorExportModal: { template: '<div data-testid="stub-export-modal" />' },
  CreatorPublishWizardModal: { template: '<div data-testid="stub-publish-modal" />' },
  CreatorPublishHistoryModal: { template: '<div data-testid="stub-publish-history-modal" />' },
};

describe('CreatorPageLayout', () => {
  test('renders page shell and major sections', async () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } });
    await flushPromises();
    expect(wrapper.find(byTestid('creator-page')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-creator-header')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-creator-banners')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-intervention-banner')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-creator-workspace')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-write-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-pulse-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-memory-panel')).exists()).toBe(true);
  });

  test('renders async modal components', async () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } });
    await flushPromises();
    // Async components should be resolved and rendered
    expect(wrapper.find(byTestid('stub-volume-share-modals')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-export-modal')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-publish-modal')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-publish-history-modal')).exists()).toBe(true);
  });

  test('invokes useCreatorPage on setup', () => {
    useCreatorPage.mockClear();
    mount(CreatorPageLayout, { global: { stubs: layoutStubs } });
    expect(useCreatorPage).toHaveBeenCalledTimes(1);
  });

  test('has correct page structure class', () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } });
    expect(wrapper.find(byTestid('creator-page')).classes()).toContain('creator-page');
    expect(wrapper.find(byTestid('creator-page')).classes()).toContain('l1-page');
  });
});
