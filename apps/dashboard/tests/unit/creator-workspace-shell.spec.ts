// tests/unit/creator-workspace-shell.spec.ts — CreatorWorkspaceShell 行为测试

import { describe, test, expect, vi } from 'vitest'
import { ref, computed, reactive } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import CreatorWorkspaceShell from '../../src/components/creator/CreatorWorkspaceShell.vue'
import { byTestid } from '../helpers/by-testid'
import { CREATOR_PAGE_CHROME_KEY } from '../../src/components/creator/creatorPageChromeKey.js'

function mountShell(overrides = {}) {
  const raw = {
    overview: ref({ creation_mode: 'companion' }),
    workspaceTabsEnabled: true,
    workspaceActiveTab: ref('write'),
    workspacePrimaryTabs: computed(() => [
      { id: 'write', label: '写作', icon: '✏️' },
      { id: 'pulse', label: '脉动', icon: '🌀' },
    ]),
    workspaceSecondaryTabs: computed(() => [
      { id: 'settings', label: '设置', icon: '⚙️' },
    ]),
    workspaceDrawerTabs: computed(() => []),
    deskDrawerEnabled: false,
    deskDrawerPanel: ref(null),
    deskDrawerOpen: ref(false),
    workspaceTabBadges: computed(() => ({})),
    setWorkspaceTab: vi.fn(),
    openDeskDrawer: vi.fn(),
    closeDeskDrawer: vi.fn(),
    isWorkspaceColumnVisible: vi.fn(() => true),
    isDeskDrawerColumn: vi.fn(() => false),
    ...overrides,
  }

  // Wrap in reactive for auto-unwrapping (matching production behavior)
  const chrome = reactive(raw)

  // Wire up setWorkspaceTab to update activeTab
  raw.setWorkspaceTab.mockImplementation((tab) => {
    raw.workspaceActiveTab.value = tab
  })

  const wrapper = mount(CreatorWorkspaceShell, {
    global: {
      provide: { [CREATOR_PAGE_CHROME_KEY]: chrome },
    },
    slots: {
      default: '<div data-testid="slot-content">Slot Content</div>',
    },
  })
  return { wrapper, chrome, raw }
}

describe('CreatorWorkspaceShell', () => {
  test('renders workspace tabs when overview exists', async () => {
    const { wrapper } = mountShell()
    await flushPromises()
    expect(wrapper.find(byTestid('creator-workspace-tabs')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-workspace-tab-write')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-workspace-tab-pulse')).exists()).toBe(true)
  })

  test('renders secondary tabs', async () => {
    const { wrapper } = mountShell()
    await flushPromises()
    expect(wrapper.find(byTestid('creator-workspace-secondary-tabs')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-workspace-tab-settings')).exists()).toBe(true)
  })

  test('renders slot content', async () => {
    const { wrapper } = mountShell()
    await flushPromises()
    expect(wrapper.find(byTestid('slot-content')).exists()).toBe(true)
  })

  test('hides tabs when workspaceTabsEnabled is false', async () => {
    const { wrapper } = mountShell({ workspaceTabsEnabled: false })
    await flushPromises()
    expect(wrapper.find(byTestid('creator-workspace-tabs')).exists()).toBe(false)
    expect(wrapper.find(byTestid('creator-grid')).exists()).toBe(true)
  })

  test('hides everything when no overview', async () => {
    const { wrapper } = mountShell({ overview: ref(null) })
    await flushPromises()
    expect(wrapper.find(byTestid('creator-workspace-tabs')).exists()).toBe(false)
    expect(wrapper.find(byTestid('creator-grid')).exists()).toBe(false)
  })

  test('clicking secondary tab calls setWorkspaceTab', async () => {
    const { wrapper, raw } = mountShell()
    await flushPromises()
    await wrapper.find(byTestid('creator-workspace-tab-settings')).trigger('click')
    expect(raw.setWorkspaceTab).toHaveBeenCalledWith('settings')
  })

  test('active tab has correct class', async () => {
    const { wrapper } = mountShell()
    await flushPromises()
    const activeTab = wrapper.find(byTestid('creator-workspace-tab-write'))
    expect(activeTab.classes()).toContain('hub-tab--active')
  })

  test('switching active tab updates UI', async () => {
    const { wrapper, raw } = mountShell()
    await flushPromises()
    raw.workspaceActiveTab.value = 'pulse'
    await flushPromises()
    const writeTab = wrapper.find(byTestid('creator-workspace-tab-write'))
    const pulseTab = wrapper.find(byTestid('creator-workspace-tab-pulse'))
    expect(writeTab.classes()).not.toContain('hub-tab--active')
    expect(pulseTab.classes()).toContain('hub-tab--active')
  })

  test('renders desk drawer triggers when enabled', async () => {
    const { wrapper } = mountShell({
      deskDrawerEnabled: true,
      workspaceDrawerTabs: computed(() => [
        { id: 'outline', label: '大纲', icon: '📋' },
      ]),
    })
    await flushPromises()
    expect(wrapper.find(byTestid('creator-desk-drawer-triggers')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-desk-drawer-outline')).exists()).toBe(true)
  })

  test('clicking drawer trigger calls openDeskDrawer', async () => {
    const { wrapper, raw } = mountShell({
      deskDrawerEnabled: true,
      workspaceDrawerTabs: computed(() => [
        { id: 'outline', label: '大纲', icon: '📋' },
      ]),
    })
    await flushPromises()
    await wrapper.find(byTestid('creator-desk-drawer-outline')).trigger('click')
    expect(raw.openDeskDrawer).toHaveBeenCalledWith('outline')
  })

  test('shows backdrop when desk drawer is open', async () => {
    const { wrapper } = mountShell({
      deskDrawerEnabled: true,
      workspaceDrawerTabs: computed(() => [
        { id: 'outline', label: '大纲', icon: '📋' },
      ]),
      deskDrawerOpen: ref(true),
    })
    await flushPromises()
    expect(wrapper.find(byTestid('creator-desk-drawer-backdrop')).exists()).toBe(true)
  })

  test('clicking backdrop closes drawer', async () => {
    const { wrapper, raw } = mountShell({
      deskDrawerEnabled: true,
      workspaceDrawerTabs: computed(() => [
        { id: 'outline', label: '大纲', icon: '📋' },
      ]),
      deskDrawerOpen: ref(true),
    })
    await flushPromises()
    await wrapper.find(byTestid('creator-desk-drawer-backdrop')).trigger('click')
    expect(raw.closeDeskDrawer).toHaveBeenCalled()
  })
})
