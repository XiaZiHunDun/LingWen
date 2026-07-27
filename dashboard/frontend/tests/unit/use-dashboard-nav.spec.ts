// tests/unit/use-dashboard-nav.spec.ts — workspace deep link + reviewer nav

import { describe, test, expect, beforeEach, vi } from 'vitest'
import { useNavStore } from '../../src/stores/useNavStore.js'

describe('useNavStore workspace deep link', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  test('navigateTo write with workspace=pulse updates URL', () => {
    const store = useNavStore()
    store.navigateTo('write', { workspace: 'pulse', clearFocus: true });
    expect(window.location.search).toContain('nav=write');
    expect(window.location.search).toContain('workspace=pulse');
    expect(store.$state.focusCreatorWorkspace).toBe('pulse');
  });

  test('setCreatorWorkspace write removes workspace param', () => {
    const store = useNavStore()
    store.navigateTo('creator', { workspace: 'settings' });
    store.setCreatorWorkspace('write');
    expect(window.location.search).not.toContain('workspace=');
  });

  test('reviewer blocked from creator lands on inbox', () => {
    window.history.replaceState({}, '', '/?role=reviewer');
    const store = useNavStore()
    store.navigateTo('creator', { clearFocus: true });
    expect(store.$state.activeNav).toBe('inbox');
  });

  test('reviewer default nav without param is inbox', () => {
    window.history.replaceState({}, '', '/?role=reviewer');
    const store = useNavStore()
    expect(store.$state.activeNav).toBe('inbox');
  });

  test('clearFocus clears workspace deep link', () => {
    const store = useNavStore()
    store.navigateTo('creator', { workspace: 'pulse' });
    store.navigateTo('inbox', { clearFocus: true, tab: 'decisions' });
    expect(store.$state.focusCreatorWorkspace).toBeNull();
    expect(window.location.search).not.toContain('workspace=');
  });

  test('navigateTo write with clearFocus clears workspace deep link', () => {
    const store = useNavStore()
    store.navigateTo('creator', { workspace: 'pulse' });
    store.navigateTo('write', { clearFocus: true });
    expect(store.$state.focusCreatorWorkspace).toBeNull();
    expect(window.location.search).toContain('nav=write');
    expect(window.location.search).not.toContain('workspace=');
  });

  test('popstate restores workspace from URL', () => {
    window.history.replaceState({}, '', '/?nav=write&workspace=pulse');
    const store = useNavStore()
    store.syncNavFromBrowserUrl();
    expect(store.$state.activeNav).toBe('creator');
    expect(store.$state.focusCreatorWorkspace).toBe('pulse');
  });

  test('navigateTo produce/inbox/insight updates tab params', () => {
    const store = useNavStore()
    store.navigateTo('produce', { tab: 'workflows', clearFocus: true });
    expect(store.$state.produceTab).toBe('workflows');
    expect(window.location.search).toContain('tab=workflows');
    store.navigateTo('inbox', { tab: 'ripples' });
    expect(store.$state.inboxTab).toBe('ripples');
    store.navigateTo('insight', { tab: 'analytics' });
    expect(store.$state.insightTab).toBe('analytics');
  });

  test('legacy nav ids map to grouped tabs', () => {
    const store = useNavStore()
    store.navigateTo('studio', { clearFocus: true });
    expect(store.$state.activeNav).toBe('produce');
    expect(store.$state.produceTab).toBe('studio');
    store.navigateTo('decisions');
    expect(store.$state.activeNav).toBe('inbox');
    expect(store.$state.inboxTab).toBe('decisions');
  });

  test('wizard and chapter deep links sync to URL', () => {
    const store = useNavStore()
    store.navigateTo('creator', {
      chapter: 3,
      wizard: true,
      wizardStep: 'pillars',
      wizardDone: ['init'],
      wizardNotes: { tone: '克制' },
      workspace: 'settings',
    });
    expect(store.$state.focusChapter).toBe(3);
    expect(store.$state.focusWizard).toBe(true);
    expect(store.$state.focusWizardStep).toBe('pillars');
    expect(store.$state.focusWizardDone).toEqual(['init']);
    expect(store.$state.focusWizardNotes).toEqual({ tone: '克制' });
    expect(window.location.search).toContain('chapter=3');
    expect(window.location.search).toContain('wizard=1');
    expect(window.location.search).toContain('workspace=settings');
  });

  test('setProduceTab setInboxTab setInsightTab guard invalid ids', () => {
    const store = useNavStore()
    store.setProduceTab('not-a-tab');
    store.setInboxTab('invalid');
    store.setInsightTab('nope');
    expect(store.$state.produceTab).not.toBe('not-a-tab');
    store.setProduceTab('chapters');
    store.setInboxTab('decisions');
    store.setInsightTab('overview');
    expect(store.$state.produceTab).toBe('chapters');
    expect(store.$state.inboxTab).toBe('decisions');
    expect(store.$state.insightTab).toBe('overview');
  });

  test('setWizardDeepLink toggles wizard state', () => {
    const store = useNavStore()
    store.setWizardDeepLink(true, 'outline', ['pillars'], { note: 'x' });
    expect(store.$state.focusWizard).toBe(true);
    expect(store.$state.focusWizardStep).toBe('outline');
    store.setWizardDeepLink(false);
    expect(store.$state.focusWizard).toBe(false);
  });

  test('syncNavFromBrowserUrl restores wizard notes from encoded param', () => {
    const notes = btoa(unescape(encodeURIComponent(JSON.stringify({ mood: '悬疑' }))));
    window.history.replaceState({}, '', `/?nav=creator&wizard=1&notes=${notes}&decision=d-1`);
    const store = useNavStore()
    store.syncNavFromBrowserUrl();
    expect(store.$state.focusWizardNotes).toEqual({ mood: '悬疑' });
    expect(store.$state.focusDecisionId).toBe('d-1');
  });

  test('invalid nav param falls back to ask', () => {
    window.history.replaceState({}, '', '/?nav=not-a-real-nav');
    const store = useNavStore()
    store.syncNavFromBrowserUrl();
    expect(store.$state.activeNav).toBe('ask');
  });
});
