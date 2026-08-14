/**
 * Creator module shared types for injection contexts
 */
import type { ComputedRef, InjectionKey, Ref } from 'vue';

/** Creator write context — injected via CREATOR_WRITE_KEY */
export interface CreatorWriteContext {
  chapterBodyDraft: Ref<string>;
  openOutline: () => void;
  openStats: () => void;
  wb: {
    creationMode: Ref<string>;
    workbenchEnabled: Ref<boolean>;
    leftPanelCollapsed: Ref<boolean>;
    startQuickWrite: () => void;
    updateCreationMode: (mode: string) => Promise<void>;
    agent?: {
      status: Ref<string>;
      isStreaming: Ref<boolean>;
      lastError: Ref<string | null>;
    };
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

/** Creator page chrome context — injected via CREATOR_PAGE_CHROME_KEY */
export interface CreatorPageChromeContext {
  overview: Ref<Record<string, unknown> | null>;
  workspaceTabsEnabled: boolean;
  workspaceActiveTab: Ref<string>;
  workspacePrimaryTabs: ComputedRef<Array<{ id: string; label: string }>>;
  workspaceSecondaryTabs: ComputedRef<Array<{ id: string; label: string }>>;
  workspaceDrawerTabs: ComputedRef<Array<{ id: string; label: string }>>;
  deskDrawerEnabled: boolean;
  deskDrawerPanel: Ref<string | null>;
  deskDrawerOpen: Ref<boolean>;
  workspaceTabBadges: ComputedRef<Record<string, number> | null>;
  setWorkspaceTab: (tabId: string) => void;
  openDeskDrawer: (tabId: string) => void;
  closeDeskDrawer: () => void;
  isWorkspaceColumnVisible?: (columnId: string) => boolean;
  isDeskDrawerColumn?: (columnId: string) => boolean;
  [key: string]: unknown;
}

/** Creator product tools context — injected via CREATOR_PRODUCT_TOOLS_KEY */
export interface CreatorProductToolsContext {
  preferences: Ref<Record<string, unknown>>;
  exportConfig: Ref<Record<string, unknown>>;
  publishState: Ref<Record<string, unknown>>;
  interventionState: Ref<Record<string, unknown>>;
  updatePreference: (key: string, value: unknown) => Promise<void>;
  triggerExport: (format?: string) => Promise<void>;
  triggerPublish: (target?: string) => Promise<void>;
  [key: string]: unknown;
}

export type CreatorWriteKey = InjectionKey<CreatorWriteContext>;
export type CreatorPageChromeKey = InjectionKey<CreatorPageChromeContext>;
export type CreatorProductToolsKey = InjectionKey<CreatorProductToolsContext>;
