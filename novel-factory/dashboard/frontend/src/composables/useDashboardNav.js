/**
 * Phase 9.83 F75: dashboard nav + URL deep link (?nav=decisions&chapter=5&decision=abc).
 */
import { ref } from 'vue';

const VALID_NAV = [
  'creator',
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

function readWizardFromUrl() {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location.search).get('wizard') === '1';
}

function syncNavUrl(activeNav, chapter, decisionId, wizard) {
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
  if (wizard) {
    url.searchParams.set('wizard', '1');
  } else {
    url.searchParams.delete('wizard');
  }
  window.history.replaceState(window.history.state, '', url.toString());
}

const activeNav = ref(readNavFromUrl());
const focusChapter = ref(readChapterFromUrl());
const focusDecisionId = ref(readDecisionFromUrl());
const focusWizard = ref(readWizardFromUrl());

/**
 * @param {string} nav
 * @param {{ chapter?: number|null, decisionId?: string|null, clearFocus?: boolean, wizard?: boolean }} [opts]
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
  if (opts.wizard !== undefined) focusWizard.value = Boolean(opts.wizard);
  syncNavUrl(activeNav.value, focusChapter.value, focusDecisionId.value, focusWizard.value);
}

function setWizardDeepLink(open) {
  focusWizard.value = Boolean(open);
  syncNavUrl(activeNav.value, focusChapter.value, focusDecisionId.value, focusWizard.value);
}

function clearDecisionFocus() {
  focusChapter.value = null;
  focusDecisionId.value = null;
  syncNavUrl(activeNav.value, null, null, focusWizard.value);
}

export function useDashboardNav() {
  return {
    activeNav,
    focusChapter,
    focusDecisionId,
    focusWizard,
    navigateTo,
    setWizardDeepLink,
    clearDecisionFocus,
  };
}
