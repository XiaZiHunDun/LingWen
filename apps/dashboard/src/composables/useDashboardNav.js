import { unref } from 'vue';
import { useNavStore } from '../stores/useNavStore.js';

function navValue(store, key) {
  return unref(store[key]);
}

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
    activeNav: navValue(store, 'activeNav'),
    produceTab: navValue(store, 'produceTab'),
    inboxTab: navValue(store, 'inboxTab'),
    insightTab: navValue(store, 'insightTab'),
    focusChapter: navValue(store, 'focusChapter'),
    focusDecisionId: navValue(store, 'focusDecisionId'),
    focusWizard: navValue(store, 'focusWizard'),
    focusWizardStep: navValue(store, 'focusWizardStep'),
    focusWizardDone: navValue(store, 'focusWizardDone'),
    focusWizardNotes: navValue(store, 'focusWizardNotes'),
    focusCreatorWorkspace: navValue(store, 'focusCreatorWorkspace'),
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