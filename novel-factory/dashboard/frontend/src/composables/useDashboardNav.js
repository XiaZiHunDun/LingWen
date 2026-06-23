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
  const params = new URLSearchParams(window.location.search);
  return params.get('wizard') === '1' || Boolean(params.get('step'));
}

function readWizardStepFromUrl() {
  if (typeof window === 'undefined') return null;
  const step = new URLSearchParams(window.location.search).get('step');
  return step && step.trim() ? step.trim() : null;
}

function syncNavUrl(activeNav, chapter, decisionId, wizard, wizardStep) {
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
  if (wizardStep) {
    url.searchParams.set('step', wizardStep);
  } else {
    url.searchParams.delete('step');
  }
  window.history.replaceState(window.history.state, '', url.toString());
}

const activeNav = ref(readNavFromUrl());
const focusChapter = ref(readChapterFromUrl());
const focusDecisionId = ref(readDecisionFromUrl());
const focusWizard = ref(readWizardFromUrl());
const focusWizardStep = ref(readWizardStepFromUrl());

/**
 * @param {string} nav
 * @param {{ chapter?: number|null, decisionId?: string|null, clearFocus?: boolean, wizard?: boolean, wizardStep?: string|null }} [opts]
 */
function navigateTo(nav, opts = {}) {
  activeNav.value = VALID_NAV.includes(nav) ? nav : 'overview';
  if (opts.clearFocus) {
    focusChapter.value = null;
    focusDecisionId.value = null;
    focusWizardStep.value = null;
  } else {
    if (opts.chapter !== undefined) focusChapter.value = opts.chapter;
    if (opts.decisionId !== undefined) focusDecisionId.value = opts.decisionId;
    if (opts.wizardStep !== undefined) focusWizardStep.value = opts.wizardStep;
  }
  if (opts.wizard !== undefined) focusWizard.value = Boolean(opts.wizard);
  if (opts.wizardStep) focusWizard.value = true;
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
  );
}

function setWizardDeepLink(open, wizardStep) {
  focusWizard.value = Boolean(open);
  if (wizardStep !== undefined) {
    focusWizardStep.value = wizardStep || null;
  }
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
  );
}

function clearDecisionFocus() {
  focusChapter.value = null;
  focusDecisionId.value = null;
  syncNavUrl(activeNav.value, null, null, focusWizard.value, focusWizardStep.value);
}

export function useDashboardNav() {
  return {
    activeNav,
    focusChapter,
    focusDecisionId,
    focusWizard,
    focusWizardStep,
    navigateTo,
    setWizardDeepLink,
    clearDecisionFocus,
  };
}
