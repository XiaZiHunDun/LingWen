/**
 * Phase 9.83 F75: dashboard nav + URL deep link (?nav=decisions&chapter=5&decision=abc).
 */
import { ref } from 'vue';

const VALID_NAV = [
  'studio',
  'overview',
  'decisions',
  'workflows',
  'chapters',
  'analytics',
  'ripples',
  'cascade-runs',
  'settings',
];

function readNavFromUrl() {
  if (typeof window === 'undefined') return 'overview';
  const nav = new URLSearchParams(window.location.search).get('nav');
  return VALID_NAV.includes(nav) ? nav : 'overview';
}

function readChapterFromUrl() {
  if (typeof window === 'undefined') return null;
  const raw = new URLSearchParams(window.location.search).get('chapter');
  if (raw == null || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) && n >= 1 ? n : null;
}

function readDecisionFromUrl() {
  if (typeof window === 'undefined') return null;
  const id = new URLSearchParams(window.location.search).get('decision');
  return id && id.trim() ? id.trim() : null;
}

function syncNavUrl(activeNav, chapter, decisionId) {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  if (activeNav && activeNav !== 'overview') {
    url.searchParams.set('nav', activeNav);
  } else {
    url.searchParams.delete('nav');
  }
  if (chapter != null) {
    url.searchParams.set('chapter', String(chapter));
  } else {
    url.searchParams.delete('chapter');
  }
  if (decisionId) {
    url.searchParams.set('decision', decisionId);
  } else {
    url.searchParams.delete('decision');
  }
  window.history.replaceState(window.history.state, '', url.toString());
}

const activeNav = ref(readNavFromUrl());
const focusChapter = ref(readChapterFromUrl());
const focusDecisionId = ref(readDecisionFromUrl());

/**
 * @param {string} nav
 * @param {{ chapter?: number|null, decisionId?: string|null, clearFocus?: boolean }} [opts]
 */
function navigateTo(nav, opts = {}) {
  activeNav.value = VALID_NAV.includes(nav) ? nav : 'overview';
  if (opts.clearFocus) {
    focusChapter.value = null;
    focusDecisionId.value = null;
  } else {
    if (opts.chapter !== undefined) focusChapter.value = opts.chapter;
    if (opts.decisionId !== undefined) focusDecisionId.value = opts.decisionId;
  }
  syncNavUrl(activeNav.value, focusChapter.value, focusDecisionId.value);
}

function clearDecisionFocus() {
  focusChapter.value = null;
  focusDecisionId.value = null;
  syncNavUrl(activeNav.value, null, null);
}

export function useDashboardNav() {
  return {
    activeNav,
    focusChapter,
    focusDecisionId,
    navigateTo,
    clearDecisionFocus,
  };
}
