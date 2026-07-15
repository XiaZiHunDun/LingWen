// tests/unit/use-dashboard-nav.spec.ts — workspace deep link + reviewer nav

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'

describe('useDashboardNav workspace deep link', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  async function loadNav() {
    return import('../../src/composables/useDashboardNav.js').then((m) => m.useDashboardNav());
  }

  test('navigateTo write with workspace=pulse updates URL', async () => {
    const { navigateTo, focusCreatorWorkspace } = await loadNav();
    navigateTo('write', { workspace: 'pulse', clearFocus: true });
    expect(window.location.search).toContain('nav=write');
    expect(window.location.search).toContain('workspace=pulse');
    expect(focusCreatorWorkspace.value).toBe('pulse');
  });

  test('setCreatorWorkspace write removes workspace param', async () => {
    const { navigateTo, setCreatorWorkspace } = await loadNav();
    navigateTo('creator', { workspace: 'settings' });
    setCreatorWorkspace('write');
    expect(window.location.search).not.toContain('workspace=');
  });

  test('reviewer blocked from creator lands on inbox', async () => {
    window.history.replaceState({}, '', '/?role=reviewer');
    vi.resetModules();
    const { useDashboardNav } = await import('../../src/composables/useDashboardNav.js');
    const { navigateTo, activeNav } = useDashboardNav();
    navigateTo('creator', { clearFocus: true });
    expect(activeNav.value).toBe('inbox');
  });

  test('reviewer default nav without param is inbox', async () => {
    window.history.replaceState({}, '', '/?role=reviewer');
    vi.resetModules();
    const { useDashboardNav } = await import('../../src/composables/useDashboardNav.js');
    const { activeNav } = useDashboardNav();
    expect(activeNav.value).toBe('inbox');
  });

  test('clearFocus clears workspace deep link', async () => {
    const { navigateTo, focusCreatorWorkspace } = await loadNav();
    navigateTo('creator', { workspace: 'pulse' });
    navigateTo('inbox', { clearFocus: true, tab: 'decisions' });
    expect(focusCreatorWorkspace.value).toBeNull();
    expect(window.location.search).not.toContain('workspace=');
  });

  test('navigateTo write with clearFocus clears workspace deep link', async () => {
    const { navigateTo, focusCreatorWorkspace } = await loadNav();
    navigateTo('creator', { workspace: 'pulse' });
    navigateTo('write', { clearFocus: true });
    expect(focusCreatorWorkspace.value).toBeNull();
    expect(window.location.search).toContain('nav=write');
    expect(window.location.search).not.toContain('workspace=');
  });

  test('popstate restores workspace from URL', async () => {
    const { syncNavFromBrowserUrl, focusCreatorWorkspace, activeNav } = await loadNav();
    window.history.replaceState({}, '', '/?nav=write&workspace=pulse');
    syncNavFromBrowserUrl();
    expect(activeNav.value).toBe('creator');
    expect(focusCreatorWorkspace.value).toBe('pulse');
  });

  test('navigateTo produce/inbox/insight updates tab params', async () => {
    const { navigateTo, produceTab, inboxTab, insightTab } = await loadNav();
    navigateTo('produce', { tab: 'workflows', clearFocus: true });
    expect(produceTab.value).toBe('workflows');
    expect(window.location.search).toContain('tab=workflows');
    navigateTo('inbox', { tab: 'ripples' });
    expect(inboxTab.value).toBe('ripples');
    navigateTo('insight', { tab: 'analytics' });
    expect(insightTab.value).toBe('analytics');
  });

  test('legacy nav ids map to grouped tabs', async () => {
    const { navigateTo, activeNav, produceTab, inboxTab } = await loadNav();
    navigateTo('studio', { clearFocus: true });
    expect(activeNav.value).toBe('produce');
    expect(produceTab.value).toBe('studio');
    navigateTo('decisions');
    expect(activeNav.value).toBe('inbox');
    expect(inboxTab.value).toBe('decisions');
  });

  test('wizard and chapter deep links sync to URL', async () => {
    const {
      navigateTo,
      focusChapter,
      focusWizard,
      focusWizardStep,
      focusWizardDone,
      focusWizardNotes,
    } = await loadNav();
    navigateTo('creator', {
      chapter: 3,
      wizard: true,
      wizardStep: 'pillars',
      wizardDone: ['init'],
      wizardNotes: { tone: '克制' },
      workspace: 'settings',
    });
    expect(focusChapter.value).toBe(3);
    expect(focusWizard.value).toBe(true);
    expect(focusWizardStep.value).toBe('pillars');
    expect(focusWizardDone.value).toEqual(['init']);
    expect(focusWizardNotes.value).toEqual({ tone: '克制' });
    expect(window.location.search).toContain('chapter=3');
    expect(window.location.search).toContain('wizard=1');
    expect(window.location.search).toContain('workspace=settings');
  });

  test('setProduceTab setInboxTab setInsightTab guard invalid ids', async () => {
    const { setProduceTab, setInboxTab, setInsightTab, produceTab, inboxTab, insightTab } = await loadNav();
    setProduceTab('not-a-tab');
    setInboxTab('invalid');
    setInsightTab('nope');
    expect(produceTab.value).not.toBe('not-a-tab');
    setProduceTab('chapters');
    setInboxTab('decisions');
    setInsightTab('overview');
    expect(produceTab.value).toBe('chapters');
    expect(inboxTab.value).toBe('decisions');
    expect(insightTab.value).toBe('overview');
  });

  test('setWizardDeepLink toggles wizard state', async () => {
    const { setWizardDeepLink, focusWizard, focusWizardStep } = await loadNav();
    setWizardDeepLink(true, 'outline', ['pillars'], { note: 'x' });
    expect(focusWizard.value).toBe(true);
    expect(focusWizardStep.value).toBe('outline');
    setWizardDeepLink(false);
    expect(focusWizard.value).toBe(false);
  });

  test('syncNavFromBrowserUrl restores wizard notes from encoded param', async () => {
    const notes = btoa(unescape(encodeURIComponent(JSON.stringify({ mood: '悬疑' }))));
    window.history.replaceState({}, '', `/?nav=creator&wizard=1&notes=${notes}&decision=d-1`);
    const { syncNavFromBrowserUrl, focusWizardNotes, focusDecisionId } = await loadNav();
    syncNavFromBrowserUrl();
    expect(focusWizardNotes.value).toEqual({ mood: '悬疑' });
    expect(focusDecisionId.value).toBe('d-1');
  });

  test('invalid nav param falls back to ask', async () => {
    window.history.replaceState({}, '', '/?nav=not-a-real-nav');
    const { syncNavFromBrowserUrl, activeNav } = await loadNav();
    syncNavFromBrowserUrl();
    expect(activeNav.value).toBe('ask');
  });
});
