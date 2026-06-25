/**
 * Phase 9.83 F75 + Phase B/D: dashboard nav + URL deep link.
 * ?nav=produce&tab=studio | ?nav=inbox&tab=decisions | ?nav=insight&tab=overview
 * ?nav=creator&workspace=pulse — creator workspace tab deep link
 * ?role=reviewer — external reviewer (insight read-only)
 */
import { ref } from 'vue';
import {
  LEGACY_INBOX_NAV_IDS,
  LEGACY_INSIGHT_NAV_IDS,
  LEGACY_PRODUCE_NAV_IDS,
  PRODUCE_TABS,
  INBOX_TABS,
  INSIGHT_TABS,
} from '../config/dashboardNav.js';

const PRODUCE_TAB_IDS = PRODUCE_TABS.map((t) => t.id);
const INBOX_TAB_IDS = INBOX_TABS.map((t) => t.id);
const INSIGHT_TAB_IDS = INSIGHT_TABS.map((t) => t.id);

export const CREATOR_WORKSPACE_IDS = ['write', 'pulse', 'settings'];

const VALID_NAV = [
  'today',
  'creator',
  'produce',
  'inbox',
  'insight',
  'studio',
  'chapters',
  'workflows',
  'decisions',
  'ripples',
  'overview',
  'analytics',
  'cascade-runs',
  'settings',
];

const REVIEWER_BLOCKED_NAV = new Set(['creator', 'produce', 'settings', 'cascade-runs', 'studio', 'chapters', 'workflows']);

function canonicalNav(nav) {
  if (!nav) return 'today';
  if (LEGACY_PRODUCE_NAV_IDS.includes(nav)) return 'produce';
  if (LEGACY_INBOX_NAV_IDS.includes(nav)) return 'inbox';
  if (LEGACY_INSIGHT_NAV_IDS.includes(nav)) return 'insight';
  return nav;
}

function readRawNavFromUrl() {
  if (typeof window === 'undefined') return null;
  return new URLSearchParams(window.location.search).get('nav');
}

function isReviewerUrl() {
  if (typeof window === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  return params.get('role') === 'reviewer' || params.get('review') === '1';
}

function readProduceTab(rawNav) {
  if (typeof window === 'undefined') return 'studio';
  const tab = new URLSearchParams(window.location.search).get('tab');
  if (tab && PRODUCE_TAB_IDS.includes(tab)) return tab;
  if (rawNav && LEGACY_PRODUCE_NAV_IDS.includes(rawNav)) return rawNav;
  return 'studio';
}

function readInboxTab(rawNav) {
  if (typeof window === 'undefined') return 'decisions';
  const tab = new URLSearchParams(window.location.search).get('tab');
  if (tab && INBOX_TAB_IDS.includes(tab)) return tab;
  if (rawNav && LEGACY_INBOX_NAV_IDS.includes(rawNav)) return rawNav;
  return 'decisions';
}

function readInsightTab(rawNav) {
  if (typeof window === 'undefined') return 'overview';
  const tab = new URLSearchParams(window.location.search).get('tab');
  if (tab && INSIGHT_TAB_IDS.includes(tab)) return tab;
  if (rawNav && LEGACY_INSIGHT_NAV_IDS.includes(rawNav)) return rawNav;
  return 'overview';
}

function readCreatorWorkspaceFromUrl() {
  if (typeof window === 'undefined') return null;
  const ws = new URLSearchParams(window.location.search).get('workspace');
  if (ws && CREATOR_WORKSPACE_IDS.includes(ws) && ws !== 'write') return ws;
  return null;
}

function normalizeCreatorWorkspace(tab) {
  if (!tab || tab === 'write') return null;
  return CREATOR_WORKSPACE_IDS.includes(tab) ? tab : null;
}

function readNavFromUrl() {
  if (typeof window === 'undefined') return 'today';
  const raw = readRawNavFromUrl();
  if (!raw) return isReviewerUrl() ? 'inbox' : 'today';
  if (!VALID_NAV.includes(raw)) return isReviewerUrl() ? 'inbox' : 'today';
  const canonical = canonicalNav(raw);
  if (isReviewerUrl() && REVIEWER_BLOCKED_NAV.has(canonical)) {
    return 'inbox';
  }
  return canonical;
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

function preserveRoleParams(url) {
  if (typeof window === 'undefined') return;
  const current = new URL(window.location.href);
  const role = current.searchParams.get('role');
  const review = current.searchParams.get('review');
  if (role) {
    url.searchParams.set('role', role);
  } else {
    url.searchParams.delete('role');
  }
  if (!role && review === '1') {
    url.searchParams.set('review', '1');
  } else {
    url.searchParams.delete('review');
  }
}

function syncNavUrl(
  activeNav,
  chapter,
  decisionId,
  wizard,
  wizardStep,
  wizardDone,
  wizardNotes,
  produceTabVal,
  inboxTabVal,
  insightTabVal,
) {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  if (activeNav && activeNav !== 'today') {
    url.searchParams.set('nav', activeNav);
  } else {
    url.searchParams.delete('nav');
  }
  if (activeNav === 'produce') {
    url.searchParams.set('tab', produceTabVal || 'studio');
  } else if (activeNav === 'inbox') {
    url.searchParams.set('tab', inboxTabVal || 'decisions');
  } else if (activeNav === 'insight') {
    url.searchParams.set('tab', insightTabVal || 'overview');
  } else {
    url.searchParams.delete('tab');
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
  if (activeNav === 'creator') {
    const ws = focusCreatorWorkspace.value;
    if (ws && ws !== 'write' && CREATOR_WORKSPACE_IDS.includes(ws)) {
      url.searchParams.set('workspace', ws);
    } else {
      url.searchParams.delete('workspace');
    }
  } else {
    url.searchParams.delete('workspace');
  }
  preserveRoleParams(url);
  window.history.replaceState(window.history.state, '', url.toString());
}

const rawNavOnLoad = readRawNavFromUrl();
const activeNav = ref(readNavFromUrl());
const produceTab = ref(readProduceTab(rawNavOnLoad));
const inboxTab = ref(readInboxTab(rawNavOnLoad));
const insightTab = ref(readInsightTab(rawNavOnLoad));
const focusChapter = ref(readChapterFromUrl());
const focusDecisionId = ref(readDecisionFromUrl());
const focusWizard = ref(readWizardFromUrl());
const focusWizardStep = ref(readWizardStepFromUrl());
const focusWizardDone = ref(readWizardDoneFromUrl());
const focusWizardNotes = ref(readWizardNotesFromUrl());
const focusCreatorWorkspace = ref(readCreatorWorkspaceFromUrl());

function resolveNavTarget(nav) {
  if (LEGACY_PRODUCE_NAV_IDS.includes(nav)) {
    return { nav: 'produce', produceTab: nav };
  }
  if (LEGACY_INBOX_NAV_IDS.includes(nav)) {
    return { nav: 'inbox', inboxTab: nav };
  }
  if (LEGACY_INSIGHT_NAV_IDS.includes(nav)) {
    return { nav: 'insight', insightTab: nav };
  }
  return { nav };
}

function guardReviewerNav(nav) {
  if (!isReviewerUrl()) return nav;
  const canonical = canonicalNav(nav);
  if (REVIEWER_BLOCKED_NAV.has(canonical)) return 'inbox';
  return canonical;
}

/**
 * @param {string} nav
 * @param {{ chapter?: number|null, decisionId?: string|null, clearFocus?: boolean, wizard?: boolean, wizardStep?: string|null, wizardDone?: string[]|null, wizardNotes?: Record<string, string>|null, tab?: string|null, workspace?: string|null }} [opts]
 */
function navigateTo(nav, opts = {}) {
  const target = resolveNavTarget(nav);
  const resolved = guardReviewerNav(target.nav);
  activeNav.value = VALID_NAV.includes(nav) ? resolved : (isReviewerUrl() ? 'inbox' : 'today');
  if (opts.tab) {
    if (activeNav.value === 'produce' && PRODUCE_TAB_IDS.includes(opts.tab)) {
      produceTab.value = opts.tab;
    }
    if (activeNav.value === 'inbox' && INBOX_TAB_IDS.includes(opts.tab)) {
      inboxTab.value = opts.tab;
    }
    if (activeNav.value === 'insight' && INSIGHT_TAB_IDS.includes(opts.tab)) {
      insightTab.value = opts.tab;
    }
  } else if (LEGACY_PRODUCE_NAV_IDS.includes(nav)) {
    produceTab.value = nav;
  } else if (LEGACY_INBOX_NAV_IDS.includes(nav)) {
    inboxTab.value = nav;
  } else if (LEGACY_INSIGHT_NAV_IDS.includes(nav)) {
    insightTab.value = nav;
  }
  if (opts.clearFocus) {
    focusChapter.value = null;
    focusDecisionId.value = null;
    focusWizardStep.value = null;
    focusWizardDone.value = [];
    focusWizardNotes.value = {};
    focusCreatorWorkspace.value = null;
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
  if (opts.workspace !== undefined) {
    focusCreatorWorkspace.value = normalizeCreatorWorkspace(opts.workspace);
  }
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
    produceTab.value,
    inboxTab.value,
    insightTab.value,
  );
}

function setProduceTab(tab) {
  if (!PRODUCE_TAB_IDS.includes(tab)) return;
  produceTab.value = tab;
  activeNav.value = 'produce';
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
    produceTab.value,
    inboxTab.value,
    insightTab.value,
  );
}

function setInboxTab(tab) {
  if (!INBOX_TAB_IDS.includes(tab)) return;
  inboxTab.value = tab;
  activeNav.value = 'inbox';
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
    produceTab.value,
    inboxTab.value,
    insightTab.value,
  );
}

function setInsightTab(tab) {
  if (!INSIGHT_TAB_IDS.includes(tab)) return;
  insightTab.value = tab;
  activeNav.value = 'insight';
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
    produceTab.value,
    inboxTab.value,
    insightTab.value,
  );
}

function setCreatorWorkspace(tab) {
  focusCreatorWorkspace.value = normalizeCreatorWorkspace(tab);
  syncNavUrl(
    activeNav.value,
    focusChapter.value,
    focusDecisionId.value,
    focusWizard.value,
    focusWizardStep.value,
    focusWizardDone.value,
    focusWizardNotes.value,
    produceTab.value,
    inboxTab.value,
    insightTab.value,
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
    produceTab.value,
    inboxTab.value,
    insightTab.value,
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
    produceTab.value,
    inboxTab.value,
    insightTab.value,
  );
}

function syncNavFromBrowserUrl() {
  const raw = readRawNavFromUrl();
  activeNav.value = readNavFromUrl();
  produceTab.value = readProduceTab(raw);
  inboxTab.value = readInboxTab(raw);
  insightTab.value = readInsightTab(raw);
  focusChapter.value = readChapterFromUrl();
  focusDecisionId.value = readDecisionFromUrl();
  focusWizard.value = readWizardFromUrl();
  focusWizardStep.value = readWizardStepFromUrl();
  focusWizardDone.value = readWizardDoneFromUrl();
  focusWizardNotes.value = readWizardNotesFromUrl();
  focusCreatorWorkspace.value = readCreatorWorkspaceFromUrl();
}

if (typeof window !== 'undefined') {
  window.addEventListener('popstate', () => {
    syncNavFromBrowserUrl();
  });
}

export function isProduceNav(nav) {
  return nav === 'produce' || LEGACY_PRODUCE_NAV_IDS.includes(nav);
}

export function isInboxNav(nav) {
  return nav === 'inbox' || LEGACY_INBOX_NAV_IDS.includes(nav);
}

export function isInsightNav(nav) {
  return nav === 'insight' || LEGACY_INSIGHT_NAV_IDS.includes(nav);
}

export function useDashboardNav() {
  return {
    activeNav,
    produceTab,
    inboxTab,
    insightTab,
    focusChapter,
    focusDecisionId,
    focusWizard,
    focusWizardStep,
    focusWizardDone,
    focusWizardNotes,
    focusCreatorWorkspace,
    navigateTo,
    setProduceTab,
    setInboxTab,
    setInsightTab,
    setCreatorWorkspace,
    syncNavFromBrowserUrl,
    isProduceNav,
    isInboxNav,
    isInsightNav,
    setWizardDeepLink,
    buildWizardShareUrl,
    clearDecisionFocus,
  };
}
