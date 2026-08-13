import { computed } from 'vue';
import { useRoleStore } from '../stores/useRoleStore.js';

const REVIEWER_NAV_IDS = new Set(['today', 'inbox', 'insight', 'overview', 'analytics']);

function reviewerLandingNav() {
  return 'inbox';
}

export function useDashboardRole() {
  const store = useRoleStore();
  const isReviewer = computed(() => store.isReviewer);
  const isReadonlyInsight = computed(() => store.isReadonlyInsight);

  function isNavAllowedForRole(navId) {
    if (!isReviewer.value) return true;
    if (navId === 'produce') return false;
    if (navId === 'insight') return true;
    return REVIEWER_NAV_IDS.has(navId);
  }

  return {
    isReviewer,
    isReadonlyInsight,
    isNavAllowedForRole,
    reviewerLandingNav,
  };
}