/**
 * useCreatorPageChrome — 页面 chrome 上下文聚合（workspaceTabBadges + chromeContext）
 *
 * Phase 21 Task：从 useCreatorPage.js 拆出（完整实现）。
 * 负责: workspaceTabBadgesMerged computed + chromeContext 聚合 + openExportModal/openPublishWizard 包装。
 *
 * 注: 接收 main hook 的 ref 通过 deps（保持单 ref 真源）。
 */
import { computed } from 'vue';
import type { ComputedRef, Ref } from 'vue';

export interface ChromeContext {
  overview: Ref<unknown>;
  loading: Ref<boolean>;
  uiProfile: ComputedRef<Record<string, unknown>>;
  modeLabel: unknown;
  creationModeBadgeHintText: unknown;
  modeBadgeHintEnabled: unknown;
  showCreationModeBadge: unknown;
  showPageTitle: unknown;
  showHeaderPreferences: unknown;
  showHeaderPublishExport: unknown;
  showHeaderRefresh: unknown;
  showHeaderActionsRow: unknown;
  displayDeviationBadge: unknown;
  displayDeviationCount: unknown;
  showCreationModeBadgeHint: unknown;
  workspaceActiveTab: unknown;
  workspaceTabsEnabled: unknown;
  workspaceTabs: unknown;
  workspacePrimaryTabs: unknown;
  workspaceSecondaryTabs: unknown;
  workspaceDrawerTabs: unknown;
  deskDrawerEnabled: unknown;
  deskDrawerPanel: unknown;
  deskDrawerOpen: unknown;
  isDeskDrawerColumn: unknown;
  openDeskDrawer: unknown;
  closeDeskDrawer: unknown;
  workspaceTabBadges: ComputedRef<unknown>;
  setWorkspaceTab: (...args: unknown[]) => void;
  onDeviationBadgeClick: (...args: unknown[]) => void;
  error: Ref<string | null>;
  conflictMessage: Ref<string>;
  saveMessage: Ref<string>;
  refresh: () => Promise<void>;
  preferencesSummary: unknown;
  openExportModal: (...args: unknown[]) => void;
  openPublishWizard: () => void;
}

export interface CreatorPageChromeDeps {
  // 主 hook 拥有的 ref
  overview: Ref<unknown>;
  loading: Ref<boolean>;
  uiProfile: ComputedRef<Record<string, unknown>>;
  error: Ref<string | null>;
  conflictMessage: Ref<string>;
  saveMessage: Ref<string>;
  // 来自 useCreatorPageHeader 的导出
  modeLabel: unknown;
  creationModeBadgeHintText: unknown;
  modeBadgeHintEnabled: unknown;
  showCreationModeBadge: unknown;
  showPageTitle: unknown;
  showHeaderPreferences: unknown;
  showHeaderPublishExport: unknown;
  showHeaderRefresh: unknown;
  showHeaderActionsRow: unknown;
  displayDeviationBadge: unknown;
  displayDeviationCount: unknown;
  showCreationModeBadgeHint: unknown;
  // 来自 useCreatorWorkspace 的导出
  workspaceActiveTab: unknown;
  workspaceTabsEnabled: unknown;
  workspaceTabs: unknown;
  workspacePrimaryTabs: unknown;
  workspaceSecondaryTabs: unknown;
  workspaceDrawerTabs: unknown;
  deskDrawerEnabled: unknown;
  deskDrawerPanel: unknown;
  deskDrawerOpen: unknown;
  isDeskDrawerColumn: unknown;
  openDeskDrawer: unknown;
  closeDeskDrawer: unknown;
  workspaceTabBadges: ComputedRef<unknown>;
  setWorkspaceTab: (...args: unknown[]) => void;
  onDeviationBadgeClick: (...args: unknown[]) => void;
  // 来自 product tools 的导出
  settingsHasUnsavedChanges: ComputedRef<boolean>;
  preferencesSummary: unknown;
  preferencesDirty: unknown;
  openExportModal: (...args: unknown[]) => void;
  openPublishWizard: () => void;
  // refresh action
  refresh: () => Promise<void>;
}

export interface CreatorPageChromeReturn {
  workspaceTabBadgesMerged: ComputedRef<unknown>;
  chromeContext: ChromeContext;
}

export function useCreatorPageChrome(deps: CreatorPageChromeDeps): CreatorPageChromeReturn {
  const {
    overview, loading, uiProfile, error, conflictMessage, saveMessage,
    modeLabel, creationModeBadgeHintText, modeBadgeHintEnabled, showCreationModeBadge,
    showPageTitle, showHeaderPreferences, showHeaderPublishExport, showHeaderRefresh,
    showHeaderActionsRow, displayDeviationBadge, displayDeviationCount, showCreationModeBadgeHint,
    workspaceActiveTab, workspaceTabsEnabled, workspaceTabs, workspacePrimaryTabs,
    workspaceSecondaryTabs, workspaceDrawerTabs, deskDrawerEnabled, deskDrawerPanel,
    deskDrawerOpen, isDeskDrawerColumn, openDeskDrawer, closeDeskDrawer,
    workspaceTabBadges, setWorkspaceTab, onDeviationBadgeClick,
    settingsHasUnsavedChanges, preferencesSummary, preferencesDirty,
    openExportModal, openPublishWizard, refresh,
  } = deps;

  const workspaceTabBadgesMerged = computed(() => {
    const badges = { ...((workspaceTabBadges.value as Record<string, string>) || {}) };
    if (settingsHasUnsavedChanges.value || preferencesDirty) {
      badges.settings = '!';
    }
    return Object.keys(badges).length ? badges : null;
  });

  const chromeContext: ChromeContext = {
    overview,
    loading,
    uiProfile,
    modeLabel,
    creationModeBadgeHintText,
    modeBadgeHintEnabled,
    showCreationModeBadge,
    showPageTitle,
    showHeaderPreferences,
    showHeaderPublishExport,
    showHeaderRefresh,
    showHeaderActionsRow,
    displayDeviationBadge,
    displayDeviationCount,
    showCreationModeBadgeHint,
    workspaceActiveTab,
    workspaceTabsEnabled,
    workspaceTabs,
    workspacePrimaryTabs,
    workspaceSecondaryTabs,
    workspaceDrawerTabs,
    deskDrawerEnabled,
    deskDrawerPanel,
    deskDrawerOpen,
    isDeskDrawerColumn,
    openDeskDrawer,
    closeDeskDrawer,
    workspaceTabBadges: workspaceTabBadgesMerged,
    setWorkspaceTab,
    onDeviationBadgeClick,
    error,
    conflictMessage,
    saveMessage,
    refresh,
    preferencesSummary,
    openExportModal,
    openPublishWizard,
  };

  return { workspaceTabBadgesMerged, chromeContext };
}
