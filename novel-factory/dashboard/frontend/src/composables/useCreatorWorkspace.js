/**
 * Phase C: Creator workspace — task-focused tabs (写 / 脉络 / 设定).
 */
import { computed, ref, watch } from 'vue';

export const CREATOR_WORKSPACE_TABS = [
  { id: 'write', label: '写作', icon: '✍️' },
  { id: 'pulse', label: '脉络', icon: '🗺️' },
  { id: 'settings', label: '设定', icon: '📋' },
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

  const tabsEnabled = computed(() => {
    const profile = uiProfile.value;
    if (profile?.creator_workspace_tabs === false) return false;
    if (profile?.creator_workspace_tabs === true) return true;
    const mode = overview.value?.creation_mode;
    return mode === 'companion' || mode === 'advance';
  });

  function isColumnVisible(columnId) {
    if (!tabsEnabled.value) return true;
    return activeTab.value === columnId;
  }

  function setWorkspaceTab(tabId) {
    if (CREATOR_WORKSPACE_TABS.some((t) => t.id === tabId)) {
      activeTab.value = tabId;
    }
  }

  const workspaceTabBadges = displayDeviationCount
    ? computed(() => {
      if (!displayDeviationCount.value) return null;
      return { pulse: displayDeviationCount.value };
    })
    : computed(() => null);

  function onDeviationBadgeClick() {
    if (!tabsEnabled.value || !setCreatorWorkspace) return;
    setWorkspaceTab('pulse');
    setCreatorWorkspace('pulse');
  }

  if (setCreatorWorkspace) {
    watch(activeTab, (tab) => {
      if (tabsEnabled.value) {
        setCreatorWorkspace(tab);
      }
    });

    if (focusCreatorWorkspace) {
      watch(
        () => [focusCreatorWorkspace.value, tabsEnabled.value, overview.value],
        () => {
          if (!tabsEnabled.value || !focusCreatorWorkspace.value) return;
          setWorkspaceTab(focusCreatorWorkspace.value);
        },
        { immediate: true },
      );
    }
  }

  return {
    activeTab,
    tabsEnabled,
    workspaceTabs: CREATOR_WORKSPACE_TABS,
    isColumnVisible,
    setWorkspaceTab,
    workspaceTabBadges,
    onDeviationBadgeClick,
  };
}
