import { useNavStore } from '../stores/useNavStore.js';

export const CREATOR_WORKSPACE_IDS = ['write', 'pulse', 'settings'];

export function isProduceNav(nav) {
  return useNavStore().isProduceNav(nav);
}

export function isInboxNav(nav) {
  return useNavStore().isInboxNav(nav);
}

export function isInsightNav(nav) {
  return useNavStore().isInsightNav(nav);
}

export function isWriteNav(nav) {
  return useNavStore().isWriteNav(nav);
}

export function useDashboardNav() {
  const store = useNavStore();
  return {
    activeNav: store.activeNav,
    produceTab: store.produceTab,
    inboxTab: store.inboxTab,
    insightTab: store.insightTab,
    focusChapter: store.focusChapter,
    focusDecisionId: store.focusDecisionId,
    focusWizard: store.focusWizard,
    focusWizardStep: store.focusWizardStep,
    focusWizardDone: store.focusWizardDone,
    focusWizardNotes: store.focusWizardNotes,
    focusCreatorWorkspace: store.focusCreatorWorkspace,
    navigateTo: store.navigateTo.bind(store),
    setProduceTab: store.setProduceTab.bind(store),
    setInboxTab: store.setInboxTab.bind(store),
    setInsightTab: store.setInsightTab.bind(store),
    setCreatorWorkspace: store.setCreatorWorkspace.bind(store),
    syncNavFromBrowserUrl: store.syncNavFromBrowserUrl.bind(store),
    isProduceNav: store.isProduceNav.bind(store),
    isInboxNav: store.isInboxNav.bind(store),
    isInsightNav: store.isInsightNav.bind(store),
    isWriteNav: store.isWriteNav.bind(store),
    setWizardDeepLink: store.setWizardDeepLink.bind(store),
    buildWizardShareUrl: store.buildWizardShareUrl.bind(store),
    clearDecisionFocus: store.clearDecisionFocus.bind(store),
  };
}