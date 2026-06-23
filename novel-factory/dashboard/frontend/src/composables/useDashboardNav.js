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

function encodeWizardNotes(notes) {
  const filtered = Object.fromEntries(
    Object.entries(notes || {}).filter(([, value]) => String(value).trim()),
  );
  if (!Object.keys(filtered).length) return null;
  return btoa(unescape(encodeURIComponent(JSON.stringify(filtered))));
}

function readWizardNotesFromUrl() {
  if (typeof window === 'undefined') return {};
  const raw = new URLSearchParams(window.location.search).get('notes');
  if (!raw) return {};
  try {
    const json = decodeURIComponent(escape(atob(raw)));
    const parsed = JSON.parse(json);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

function readWizardFromUrl() {
  if (typeof window === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  return (
    params.get('wizard') === '1'
    || Boolean(params.get('step'))
    || Boolean(params.get('done'))
    || Boolean(params.get('notes'))
  );
}

function readWizardStepFromUrl() {
  if (typeof window === 'undefined') return null;
  const step = new URLSearchParams(window.location.search).get('step');
  return step && step.trim() ? step.trim() : null;
}

function readWizardDoneFromUrl() {
  if (typeof window === 'undefined') return [];
  const raw = new URLSearchParams(window.location.search).get('done');
  if (!raw || !raw.trim()) return [];
  return raw.split(',').map((s) => s.trim()).filter(Boolean);
}

function syncNavUrl(activeNav, chapter, decisionId, wizard, wizardStep, wizardDone, wizardNotes) {
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
  if (wizardDone && wizardDone.length) {
    url.searchParams.set('done', wizardDone.join(','));
  } else {
    url.searchParams.delete('done');
  }
  const encodedNotes = encodeWizardNotes(wizardNotes);
  if (encodedNotes) {
    url.searchParams.set('notes', encodedNotes);
  } else {
    url.searchParams.delete('notes');
  }
  window.history.replaceState(window.history.state, '', url.toString());
}

const activeNav = ref(readNavFromUrl());
const focusChapter = ref(readChapterFromUrl());
const focusDecisionId = ref(readDecisionFromUrl());
const focusWizard = ref(readWizardFromUrl());
const focusWizardStep = ref(readWizardStepFromUrl());
const focusWizardDone = ref(readWizardDoneFromUrl());
const focusWizardNotes = ref(readWizardNotesFromUrl());

/**
 * @param {string} nav
 * @param {{ chapter?: number|null, decisionId?: string|null, clearFocus?: boolean, wizard?: boolean, wizardStep?: string|null, wizardDone?: string[]|null, wizardNotes?: Record<string, string>|null }} [opts]
 */
function navigateTo(nav, opts = {}) {
  activeNav.value = VALID_NAV.includes(nav) ? nav : 'overview';
  if (opts.clearFocus) {
    focusChapter.value = null;
    focusDecisionId.value = null;
    focusWizardStep.value = null;
    focusWizardDone.value = [];
    focusWizardNotes.value = {};
  } else {
    if (opts.chapter !== undefined) focusChapter.value = opts.chapter;
    if (opts.decisionId !== undefined) focusDecisionId.value = opts.decisionId;
    if (opts.wizardStep !== undefined) focusWizardStep.value = opts.wizardStep;
    if (opts.wizardDone !== undefined) focusWizardDone.value = opts.wizardDone || [];
    if (opts.wizardNotes !== undefined) focusWizardNotes.value = opts.wizardNotes || {};
  }
  if (opts.wizard !== undefined) focusWizard.value = Boolean(opts.wizard);
  if (opts.wizardStep) focusWizard.value = true;
  if (opts.wizardDone?.length) focusWizard.value = true;
  if (opts.wizardNotes && Object.keys(opts.wizardNotes).length) focusWizard.value = true;
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
  );
}

function setWizardDeepLink(open, wizardStep, wizardDone, wizardNotes) {
  focusWizard.value = Boolean(open);
  if (wizardStep !== undefined) {
    focusWizardStep.value = wizardStep || null;
  }
  if (wizardDone !== undefined) {
    focusWizardDone.value = wizardDone || [];
  }
  if (wizardNotes !== undefined) {
    focusWizardNotes.value = wizardNotes || {};
  }
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
  );
}

function buildWizardShareUrl(completedStepIds, wizardStep, stepNotes) {
  if (typeof window === 'undefined') return '';
  const url = new URL(window.location.href);
  url.searchParams.set('nav', 'creator');
  url.searchParams.set('wizard', '1');
  const done = (completedStepIds || []).filter(Boolean);
  if (done.length) {
    url.searchParams.set('done', done.join(','));
  } else {
    url.searchParams.delete('done');
  }
  if (wizardStep) {
    url.searchParams.set('step', wizardStep);
  }
  const encodedNotes = encodeWizardNotes(stepNotes);
  if (encodedNotes) {
    url.searchParams.set('notes', encodedNotes);
  } else {
    url.searchParams.delete('notes');
  }
  return url.toString();
}

function clearDecisionFocus() {
  focusChapter.value = null;
  focusDecisionId.value = null;
  syncNavUrl(
    activeNav.value,
    null,
    null,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
  );
}

export function useDashboardNav() {
  return {
    activeNav,
    focusChapter,
    focusDecisionId,
    focusWizard,
    focusWizardStep,
    focusWizardDone,
    focusWizardNotes,
    navigateTo,
    setWizardDeepLink,
    buildWizardShareUrl,
    clearDecisionFocus,
  };
}
