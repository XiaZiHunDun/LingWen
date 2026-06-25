/**
 * Phase C: Creator workspace — task-focused tabs (写 / 脉络 / 设定).
 */
import { computed, ref } from 'vue';

export const CREATOR_WORKSPACE_TABS = [
  { id: 'write', label: '写作', icon: '✍️' },
  { id: 'pulse', label: '脉络', icon: '🗺️' },
  { id: 'settings', label: '设定', icon: '📋' },
];

/**
 * @param {import('vue').Ref<object|null>} uiProfile
 * @param {import('vue').Ref<object|null>} overview
 */
export function useCreatorWorkspace(uiProfile, overview) {
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

  return {
    activeTab,
    tabsEnabled,
    workspaceTabs: CREATOR_WORKSPACE_TABS,
    isColumnVisible,
    setWorkspaceTab,
  };
}
