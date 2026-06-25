// tests/unit/use-dashboard-nav.spec.ts — workspace deep link + reviewer nav

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'

describe('useDashboardNav workspace deep link', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  async function loadNav() {
    return import('../../src/composables/useDashboardNav.js').then((m) => m.useDashboardNav());
  }

  test('navigateTo creator with workspace=pulse updates URL', async () => {
    const { navigateTo, focusCreatorWorkspace } = await loadNav();
    navigateTo('creator', { workspace: 'pulse', clearFocus: true });
    expect(window.location.search).toContain('nav=creator');
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

  test('popstate restores workspace from URL', async () => {
    const { syncNavFromBrowserUrl, focusCreatorWorkspace, activeNav } = await loadNav();
    window.history.replaceState({}, '', '/?nav=creator&workspace=pulse');
    syncNavFromBrowserUrl();
    expect(activeNav.value).toBe('creator');
    expect(focusCreatorWorkspace.value).toBe('pulse');
  });
});
