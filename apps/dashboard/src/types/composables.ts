/**
 * Composable return types for 墨灵 Dashboard
 * Provides type definitions for composable return values
 */

/** Creator workspace tab definition */
export interface WorkspaceTab {
  id: string;
  label: string;
  icon?: string;
  disabled?: boolean;
}

/** Split tabs result */
export interface SplitTabsResult {
  primary: WorkspaceTab[];
  secondary: WorkspaceTab[];
  drawerTabs?: WorkspaceTab[];
}

/** UI profile for creator */
export interface CreatorUiProfile {
  creator_workspace_tabs?: boolean;
  creation_mode?: string;
  [key: string]: unknown;
}

/** Studio project state */
export interface StudioProjectState {
  projects: unknown[];
  activeSlug: string | null;
  loading: boolean;
  error: string | null;
}

/** Dashboard navigation state */
export interface DashboardNavState {
  currentNav: string;
  params: Record<string, unknown>;
  [key: string]: unknown;
}

/** Review decision */
export interface ReviewDecision {
  id?: string | number;
  chapter_id?: string | number;
  type?: string;
  status?: string;
  reason?: string;
  created_at?: string;
  [key: string]: unknown;
}

/** Pulse/ripple entry */
export interface PulseEntry {
  id?: string | number;
  type?: string;
  content?: string;
  severity?: string;
  related_chapter?: string | number;
  [key: string]: unknown;
}

/** Creator workspace composable return */
export interface CreatorWorkspaceReturn {
  activeTab: import('vue').Ref<string>;
  tabsEnabled: import('vue').ComputedRef<boolean>;
  workspaceTabs: import('vue').ComputedRef<WorkspaceTab[]>;
  workspacePrimaryTabs: import('vue').ComputedRef<WorkspaceTab[]>;
  workspaceSecondaryTabs: import('vue').ComputedRef<WorkspaceTab[]>;
  workspaceDrawerTabs: import('vue').ComputedRef<WorkspaceTab[]>;
  deskDrawerEnabled: import('vue').ComputedRef<boolean>;
  deskDrawerPanel: import('vue').Ref<string | null>;
  deskDrawerOpen: import('vue').ComputedRef<boolean>;
  isColumnVisible: (columnId: string) => boolean;
  isDeskDrawerColumn: (columnId: string) => boolean;
  openDeskDrawer: (tabId: string) => void;
  closeDeskDrawer: () => void;
  setWorkspaceTab: (tabId: string) => void;
  workspaceTabBadges: import('vue').ComputedRef<Record<string, number> | null>;
  onDeviationBadgeClick: () => void;
}

/** Cost window composable return */
export interface CostWindowReturn {
  costData: import('vue').Ref<unknown>;
  loading: import('vue').Ref<boolean>;
  error: import('vue').Ref<string | null>;
  startPolling: () => void;
  stopPolling: () => void;
}

/** Ripple store composable return */
export interface RippleStoreReturn {
  ripples: import('vue').Ref<unknown[]>;
  stats: import('vue').Ref<unknown>;
  loading: import('vue').Ref<boolean>;
  refresh: () => Promise<void>;
  apply: (id: string | number) => Promise<void>;
  reject: (id: string | number) => Promise<void>;
  rollback: (id: string | number) => Promise<void>;
}

/** Creator page composable return */
export interface CreatorPageReturn {
  overview: import('vue').Ref<unknown>;
  loading: import('vue').Ref<boolean>;
  uiProfile: import('vue').ComputedRef<CreatorUiProfile>;
  modeLabel: import('vue').ComputedRef<string>;
  creationModeBadgeHintText: import('vue').ComputedRef<string>;
  modeBadgeHintEnabled: import('vue').ComputedRef<boolean>;
  showCreationModeBadge: import('vue').ComputedRef<boolean>;
  showPageTitle: import('vue').ComputedRef<boolean>;
  showHeaderPreferences: import('vue').ComputedRef<boolean>;
  showHeaderPublishExport: import('vue').ComputedRef<boolean>;
  showHeaderRefresh: import('vue').ComputedRef<boolean>;
  showHeaderActionsRow: import('vue').ComputedRef<boolean>;
  displayDeviationBadge: import('vue').ComputedRef<boolean>;
  displayDeviationCount: import('vue').ComputedRef<number>;
  showCreationModeBadgeHint: import('vue').ComputedRef<boolean>;
  workspaceActiveTab: import('vue').Ref<string>;
  workspaceTabsEnabled: import('vue').ComputedRef<boolean>;
  workspaceTabs: import('vue').ComputedRef<WorkspaceTab[]>;
  workspaceTabBadges: import('vue').ComputedRef<Record<string, number> | null>;
  onDeviationBadgeClick: () => void;
  error: import('vue').Ref<unknown>;
  conflictMessage: import('vue').Ref<string>;
  saveMessage: import('vue').Ref<string>;
  refresh: () => Promise<void>;
}
