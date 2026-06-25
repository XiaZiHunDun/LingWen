// tests/unit/creator-page-layout.spec.ts — CreatorPageLayout 轻量挂载

import { describe, test, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import CreatorPageLayout from '../../src/components/creator/CreatorPageLayout.vue';
import { byTestid } from '../helpers/by-testid';

const useCreatorPage = vi.hoisted(() => vi.fn());

vi.mock('../../src/composables/useCreatorPage.js', () => ({
  useCreatorPage,
}));

const layoutStubs = {
  CreatorPageHeader: { template: '<div data-testid="stub-creator-header" />' },
  CreatorPageBanners: { template: '<div data-testid="stub-creator-banners" />' },
  CreatorWorkspaceShell: { template: '<div data-testid="stub-creator-workspace"><slot /></div>' },
  CreatorWritePanel: { template: '<div data-testid="stub-write-panel" />' },
  CreatorPulsePanel: { template: '<div data-testid="stub-pulse-panel" />' },
  CreatorSettingsPanel: { template: '<div data-testid="stub-settings-panel" />' },
  CreatorModeGuidePanel: { template: '<div data-testid="stub-mode-guide" />' },
  CreatorVolumePlanShareModals: { template: '<div data-testid="stub-volume-share-modals" />' },
  CreatorOnboardingWizardPanel: { template: '<div data-testid="stub-onboarding" />' },
};

describe('CreatorPageLayout', () => {
  test('renders page shell and major sections', () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } });
    expect(wrapper.find('.creator-page').exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-creator-header')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-creator-banners')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-creator-workspace')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-write-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-pulse-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-settings-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-mode-guide')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-volume-share-modals')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-onboarding')).exists()).toBe(true);
  });

  test('invokes useCreatorPage on setup', () => {
    useCreatorPage.mockClear();
    mount(CreatorPageLayout, { global: { stubs: layoutStubs } });
    expect(useCreatorPage).toHaveBeenCalledTimes(1);
  });
});
