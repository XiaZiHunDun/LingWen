/**
 * useCreatorWorkspace — Phase C + 面板矩阵：按 creation_mode 裁剪 Tab 与默认页
 */
import { computed, ref, watch } from 'vue';
import {
  buildCreatorWorkspaceTabs,
  resolveDefaultWorkspaceTab,
  splitHumanFirstDeskTabs,
  isDeskDrawerEnabled,
  HUMAN_FIRST_DESK_DRAWER_TAB_IDS,
} from '../config/creatorPanelMatrix.js';
import { useEffectiveCreationMode } from './useEffectiveCreationMode.js';

/** @deprecated 使用 creatorPanelMatrix.CREATOR_WORKSPACE_TAB_DEFS */
export const CREATOR_WORKSPACE_TABS = [
  { id: 'write', label: '写作', icon: '✍️' },
  { id: 'pulse', label: '脉络', icon: '🗺️' },
  { id: 'memory', label: '记忆', icon: '🧠' },
  { id: 'settings', label: '本书设定', icon: '📋' },
];

/**
 * @param {import('vue').ComputedRef<object>} uiProfile
 * @param {import('vue').Ref<object|null>} overview
 * @param {{
 *   focusCreatorWorkspace?: import('vue').Ref<string|null>,
 *   setCreatorWorkspace?: (tab: string) => void,
 *   displayDeviationCount?: import('vue').ComputedRef<number>,
 * } | undefined} nav
 */
export function useCreatorWorkspace(uiProfile, overview, nav = {}) {
  const { focusCreatorWorkspace, setCreatorWorkspace, displayDeviationCount } = nav;
  const activeTab = ref('write');
  const deskDrawerPanel = ref(null);

  const creationMode = useEffectiveCreationMode(
    computed(() => overview.value?.creation_mode ?? null),
    computed(() => (overview.value
      ? { slug: overview.value.slug, name: overview.value.name }
      : null)),
  );

  const deskDrawerEnabled = computed(() =>
    isDeskDrawerEnabled(creationMode.value, uiProfile.value),
  );

  const splitTabs = computed(() =>
    splitHumanFirstDeskTabs(creationMode.value, { deskDrawer: deskDrawerEnabled.value }),
  );

  const tabsEnabled = computed(() => {
    const profile = uiProfile.value;
    if (profile?.creator_workspace_tabs === false) return false;
    return true;
  });

  const workspaceTabs = computed(() => {
    if (!tabsEnabled.value) return [...CREATOR_WORKSPACE_TABS];
    return buildCreatorWorkspaceTabs(creationMode.value);
  });

  const workspacePrimaryTabs = computed(() => splitTabs.value.primary);

  const workspaceSecondaryTabs = computed(() => splitTabs.value.secondary);

  const workspaceDrawerTabs = computed(() => splitTabs.value.drawerTabs || []);

  const deskDrawerOpen = computed(() => Boolean(deskDrawerPanel.value));

  function syncActiveTabToMatrix() {
    if (!tabsEnabled.value || !overview.value) return;
    const ids = workspaceTabs.value.map((t) => t.id);
    if (!ids.includes(activeTab.value)) {
      activeTab.value = resolveDefaultWorkspaceTab(creationMode.value);
    }
    if (deskDrawerEnabled.value && HUMAN_FIRST_DESK_DRAWER_TAB_IDS.includes(activeTab.value)) {
      deskDrawerPanel.value = activeTab.value;
      activeTab.value = 'write';
    }
  }

  watch(
    () => creationMode.value,
    (mode, prevMode) => {
      if (!tabsEnabled.value || !mode) return;
      if (focusCreatorWorkspace?.value) return;
      if (prevMode == null || mode !== prevMode) {
        activeTab.value = resolveDefaultWorkspaceTab(mode);
        deskDrawerPanel.value = null;
      }
    },
  );

  watch(
    () => [creationMode.value, tabsEnabled.value, deskDrawerEnabled.value, workspaceTabs.value.map((t) => t.id).join(',')],
    () => {
      syncActiveTabToMatrix();
    },
    { immediate: true },
  );

  watch(deskDrawerEnabled, (enabled) => {
    if (!enabled || !tabsEnabled.value) return;
    if (HUMAN_FIRST_DESK_DRAWER_TAB_IDS.includes(activeTab.value)) {
      openDeskDrawer(activeTab.value);
    }
  });

  function isColumnVisible(columnId) {
    if (!tabsEnabled.value) return true;
    if (deskDrawerEnabled.value) {
      if (columnId === 'write') return true;
      if (HUMAN_FIRST_DESK_DRAWER_TAB_IDS.includes(columnId)) {
        return deskDrawerPanel.value === columnId;
      }
    }
    return activeTab.value === columnId;
  }

  function isDeskDrawerColumn(columnId) {
    return deskDrawerEnabled.value && HUMAN_FIRST_DESK_DRAWER_TAB_IDS.includes(columnId);
  }

  function openDeskDrawer(tabId) {
    if (!HUMAN_FIRST_DESK_DRAWER_TAB_IDS.includes(tabId)) return;
    if (!workspaceTabs.value.some((t) => t.id === tabId)) return;
    deskDrawerPanel.value = tabId;
    activeTab.value = 'write';
    if (setCreatorWorkspace) setCreatorWorkspace(tabId);
  }

  function closeDeskDrawer() {
    deskDrawerPanel.value = null;
    if (setCreatorWorkspace) setCreatorWorkspace('write');
  }

  function setWorkspaceTab(tabId) {
    if (!workspaceTabs.value.some((t) => t.id === tabId)) return;
    if (deskDrawerEnabled.value && HUMAN_FIRST_DESK_DRAWER_TAB_IDS.includes(tabId)) {
      openDeskDrawer(tabId);
      return;
    }
    deskDrawerPanel.value = null;
    activeTab.value = tabId;
  }

  const workspaceTabBadges = displayDeviationCount
    ? computed(() => {
      if (!displayDeviationCount.value) return null;
      return { pulse: displayDeviationCount.value };
    })
    : computed(() => null);

  function onDeviationBadgeClick() {
    if (!tabsEnabled.value) return;
    setWorkspaceTab('pulse');
    if (setCreatorWorkspace && !deskDrawerEnabled.value) {
      setCreatorWorkspace('pulse');
    }
  }

  if (setCreatorWorkspace) {
    watch(activeTab, (tab) => {
      if (tabsEnabled.value && !deskDrawerOpen.value) {
        setCreatorWorkspace(tab);
      }
    });

    if (focusCreatorWorkspace) {
      watch(
        () => [focusCreatorWorkspace.value, tabsEnabled.value, overview.value],
        () => {
          if (!tabsEnabled.value) return;
          if (focusCreatorWorkspace.value) {
            setWorkspaceTab(focusCreatorWorkspace.value);
            return;
          }
          if (overview.value) {
            activeTab.value = resolveDefaultWorkspaceTab(creationMode.value);
            deskDrawerPanel.value = null;
          }
        },
        { immediate: true },
      );
    }
  }

  return {
    activeTab,
    tabsEnabled,
    workspaceTabs,
    workspacePrimaryTabs,
    workspaceSecondaryTabs,
    workspaceDrawerTabs,
    deskDrawerEnabled,
    deskDrawerPanel,
    deskDrawerOpen,
    isColumnVisible,
    isDeskDrawerColumn,
    openDeskDrawer,
    closeDeskDrawer,
    setWorkspaceTab,
    workspaceTabBadges,
    onDeviationBadgeClick,
  };
}
