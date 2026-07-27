// tests/unit/creator-workspace.spec.ts — Creator workspace basic tests

import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

// Mock the composable used by CreatorPageLayout
vi.mock('../../src/composables/index.js', () => ({
  useCreatorPage: vi.fn(),
}))

// Mock all child components of CreatorPageLayout
const layoutStubs = {
  CreatorPageHeader: { template: '<div data-testid="stub-creator-header" />' },
  CreatorPageBanners: { template: '<div data-testid="stub-creator-banners" />' },
  CreatorInterventionBanner: { template: '<div data-testid="stub-intervention-banner" />' },
  CreatorWorkspaceShell: {
    template: `
      <div data-testid="stub-workspace-shell">
        <div data-testid="creator-workspace-tabs">Workspace Tabs</div>
        <div data-testid="column-write">Write Column</div>
        <div data-testid="column-pulse">Pulse Column</div>
        <div data-testid="column-settings">Settings Column</div>
        <div data-testid="creator-workspace-tab-write">Write Tab</div>
        <div data-testid="creator-workspace-tab-pulse">Pulse Tab</div>
        <slot />
      </div>
    `,
  },
  CreatorWritePanel: { template: '<div data-testid="stub-write-panel" />' },
  CreatorPulsePanel: { template: '<div data-testid="stub-pulse-panel" />' },
  CreatorMemoryPanel: { template: '<div data-testid="stub-memory-panel" />' },
  CreatorVolumePlanShareModals: { template: '<div data-testid="stub-volume-share-modals" />' },
  CreatorExportModal: { template: '<div data-testid="stub-export-modal" />' },
  CreatorPublishWizardModal: { template: '<div data-testid="stub-publish-modal" />' },
  CreatorPublishHistoryModal: { template: '<div data-testid="stub-publish-history-modal" />' },
}

import CreatorPageLayout from '../../src/components/creator/CreatorPageLayout.vue'

describe('Creator workspace tabs', () => {
  test('renders workspace structure', async () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } })
    await flushPromises()
    expect(wrapper.find(byTestid('creator-page')).exists()).toBe(true)
    expect(wrapper.find(byTestid('stub-creator-header')).exists()).toBe(true)
    expect(wrapper.find(byTestid('stub-creator-banners')).exists()).toBe(true)
    expect(wrapper.find(byTestid('stub-workspace-shell')).exists()).toBe(true)
  })

  test('workspace tabs and columns exist', async () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } })
    await flushPromises()
    expect(wrapper.find(byTestid('creator-workspace-tabs')).exists()).toBe(true)
    expect(wrapper.find(byTestid('column-write')).exists()).toBe(true)
    expect(wrapper.find(byTestid('column-pulse')).exists()).toBe(true)
    expect(wrapper.find(byTestid('column-settings')).exists()).toBe(true)
  })

  test('write and pulse tabs exist', async () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } })
    await flushPromises()
    expect(wrapper.find(byTestid('creator-workspace-tab-write')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-workspace-tab-pulse')).exists()).toBe(true)
  })

  test('modal components are rendered', async () => {
    const wrapper = mount(CreatorPageLayout, { global: { stubs: layoutStubs } })
    await flushPromises()
    expect(wrapper.find(byTestid('stub-volume-share-modals')).exists()).toBe(true)
    expect(wrapper.find(byTestid('stub-export-modal')).exists()).toBe(true)
    expect(wrapper.find(byTestid('stub-publish-modal')).exists()).toBe(true)
    expect(wrapper.find(byTestid('stub-publish-history-modal')).exists()).toBe(true)
  })
})
