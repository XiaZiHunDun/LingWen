/**
 * Phase D: dashboard role — author (default) vs reviewer (read-only insight).
 * URL: ?role=reviewer | ?review=1
 */
import { computed, ref } from 'vue';

const REVIEWER_NAV_IDS = new Set(['today', 'inbox', 'insight', 'overview', 'analytics']);

function readRoleFromUrl() {
  if (typeof window === 'undefined') return 'author';
  const params = new URLSearchParams(window.location.search);
  const role = (params.get('role') || '').trim().toLowerCase();
  if (role === 'reviewer' || params.get('review') === '1') {
    return 'reviewer';
  }
  return 'author';
}

const dashboardRole = ref(readRoleFromUrl());

const isReviewer = computed(() => dashboardRole.value === 'reviewer');
const isReadonlyInsight = computed(() => isReviewer.value);

function isNavAllowedForRole(navId) {
  if (!isReviewer.value) return true;
  if (navId === 'produce') return false;
  if (navId === 'insight') return true;
  return REVIEWER_NAV_IDS.has(navId);
}

function reviewerLandingNav() {
  return 'inbox';
}

export function useDashboardRole() {
  return {
    dashboardRole,
    isReviewer,
    isReadonlyInsight,
    isNavAllowedForRole,
    reviewerLandingNav,
  };
}
