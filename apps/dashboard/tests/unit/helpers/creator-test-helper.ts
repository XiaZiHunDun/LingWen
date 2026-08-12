// tests/unit/helpers/creator-test-helper.ts
// Shared mount helpers for Creator component tests that need injection contexts.

import { reactive, ref, computed } from 'vue'
import type { Component, App } from 'vue'
import { mount, type MountingOptions, type VueWrapper } from '@vue/test-utils'

// ---- Injection keys (re-exported for convenience) ----
export { CREATOR_WRITE_KEY } from '../../../src/components/creator/creatorWriteKey.js'
export { CREATOR_PAGE_CHROME_KEY } from '../../../src/components/creator/creatorPageChromeKey.js'
export { CREATOR_PRODUCT_TOOLS_KEY } from '../../../src/components/creator/creatorProductToolsKey.js'

import { CREATOR_WRITE_KEY } from '../../../src/components/creator/creatorWriteKey.js'
import { CREATOR_PAGE_CHROME_KEY } from '../../../src/components/creator/creatorPageChromeKey.js'
import { CREATOR_PRODUCT_TOOLS_KEY, createCreatorProductToolsContext } from '../../../src/components/creator/creatorProductToolsKey.js'

// ---- Default context factories ----

/** Creates a reactive CREATOR_WRITE_KEY context with sensible defaults */
export function createDefaultWriteContext(overrides: Record<string, unknown> = {}) {
  const raw = {
    chapterBodyDraft: ref(''),
    openOutline: () => {},
    openStats: () => {},
    wb: reactive({
      creationMode: ref('companion'),
      workbenchEnabled: ref(false),
      leftPanelCollapsed: ref(false),
      startQuickWrite: vi.fn(),
      updateCreationMode: vi.fn().mockResolvedValue(undefined),
    }),
    ...overrides,
  }
  return reactive(raw)
}

/** Creates a reactive CREATOR_PAGE_CHROME_KEY context */
export function createDefaultChromeContext(overrides: Record<string, unknown> = {}) {
  const raw = {
    overview: ref({ creation_mode: 'companion' }),
    workspaceTabsEnabled: true,
    workspaceActiveTab: ref('write'),
    workspacePrimaryTabs: computed(() => []),
    workspaceSecondaryTabs: computed(() => []),
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
  return reactive(raw)
}

// ---- Mount helpers ----

/**
 * Mount a Creator component that requires CREATOR_WRITE_KEY injection.
 * Provides default write context; pass overrides to customize.
 */
export function mountWithWriteContext<T extends Component>(
  component: T,
  options: {
    writeContext?: Record<string, unknown>
    mountOptions?: Partial<MountingOptions>
  } = {},
): VueWrapper {
  const ctx = createDefaultWriteContext(options.writeContext)
  return mount(component, {
    global: {
      provide: { [CREATOR_WRITE_KEY]: ctx },
      ...(options.mountOptions?.global || {}),
    },
    ...options.mountOptions,
  })
}

/**
 * Mount a Creator component that requires CREATOR_PAGE_CHROME_KEY injection.
 */
export function mountWithChromeContext<T extends Component>(
  component: T,
  options: {
    chromeContext?: Record<string, unknown>
    mountOptions?: Partial<MountingOptions>
  } = {},
): VueWrapper {
  const chrome = createDefaultChromeContext(options.chromeContext)
  return mount(component, {
    global: {
      provide: { [CREATOR_PAGE_CHROME_KEY]: chrome },
      ...(options.mountOptions?.global || {}),
    },
    ...options.mountOptions,
  })
}

/**
 * Mount a Creator component that requires CREATOR_PRODUCT_TOOLS_KEY injection.
 * Uses the production createCreatorProductToolsContext factory for realistic defaults.
 */
export function mountWithProductToolsContext<T extends Component>(
  component: T,
  options: {
    toolOverrides?: Record<string, unknown>
    mountOptions?: Partial<MountingOptions>
  } = {},
): VueWrapper {
  const pt = createCreatorProductToolsContext(options.toolOverrides || {})
  return mount(component, {
    global: {
      provide: { [CREATOR_PRODUCT_TOOLS_KEY]: pt },
      ...(options.mountOptions?.global || {}),
    },
    ...options.mountOptions,
  })
}

/**
 * Mount with all three main Creator contexts.
 */
export function mountWithAllCreatorContexts<T extends Component>(
  component: T,
  options: {
    writeContext?: Record<string, unknown>
    chromeContext?: Record<string, unknown>
    toolOverrides?: Record<string, unknown>
    mountOptions?: Partial<MountingOptions>
  } = {},
): VueWrapper {
  const w = createDefaultWriteContext(options.writeContext)
  const c = createDefaultChromeContext(options.chromeContext)
  const pt = createCreatorProductToolsContext(options.toolOverrides || {})
  return mount(component, {
    global: {
      provide: {
        [CREATOR_WRITE_KEY]: w,
        [CREATOR_PAGE_CHROME_KEY]: c,
        [CREATOR_PRODUCT_TOOLS_KEY]: pt,
        ...(options.mountOptions?.global || {}),
      },
      ...options.mountOptions,
    },
  })
}
