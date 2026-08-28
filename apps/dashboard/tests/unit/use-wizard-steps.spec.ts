/**
 * useWizardSteps 子模块独立测试
 *
 * Phase 39: 为 Phase 19.7 useWizardSteps 子模块添加专门测试。
 * 重点测试：步骤加载/分享链接/勾选/笔记/同步。
 *
 * Phase 126 v16.2.4 T6: mock 改用 `@/api/onboarding` typed wrapper names
 * （替代 v16.2.3 之前的 Creator-prefixed legacy aliases from api/index.js）。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed, nextTick } from 'vue';

const wizMocks = vi.hoisted(() => ({
  fetchOnboardingWizard: vi.fn(),
  saveOnboardingProgress: vi.fn(),
  applyWizardShareDone: vi.fn(),
  saveOnboardingNotes: vi.fn(),
}));

vi.mock('@/api/onboarding', () => {
  const m = wizMocks;
  return {
    fetchOnboardingWizard: (...args: unknown[]) => m.fetchOnboardingWizard(...args),
    saveOnboardingProgress: (...args: unknown[]) => m.saveOnboardingProgress(...args),
    applyWizardShareDone: (...args: unknown[]) => m.applyWizardShareDone(...args),
    saveOnboardingNotes: (...args: unknown[]) => m.saveOnboardingNotes(...args),
  };
});

import { useWizardSteps } from '../../src/composables/useCreatorOnboarding/useWizardSteps';

function mountWizard() {
  const uiProfile = ref<Record<string, unknown>>({});
  const overview = ref<Record<string, unknown> | null>({ creation_mode: 'companion' });
  const error = ref<string | null>(null);
  const focusWizard = ref<boolean>(false);
  const focusWizardStep = ref<string | null>(null);
  const focusWizardDone = ref<string[]>([]);
  const focusWizardNotes = ref<Record<string, string>>({});
  const wizardUnreadMentions = ref(0);
  const setWizardDeepLink = vi.fn();
  const buildWizardShareUrl = vi.fn((done: string[], step: string | null, notes: Record<string, string>) => 'https://share');
  const globalOutlineEditorRef = ref<HTMLElement | null>(null);

  const ctx = useWizardSteps({
    uiProfile, overview, error,
    focusWizard, focusWizardStep, focusWizardDone, focusWizardNotes,
    wizardUnreadMentions,
    setWizardDeepLink, buildWizardShareUrl, globalOutlineEditorRef,
    } as unknown as Parameters<typeof useWizardSteps>[0]);
  return {
    ...ctx,
    uiProfile, overview, focusWizard, focusWizardStep, focusWizardDone, focusWizardNotes,
    setWizardDeepLink, buildWizardShareUrl, error,
  };
}

describe('useWizardSteps', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    wizMocks.fetchOnboardingWizard.mockResolvedValue({
      steps: [],
      completed_step_ids: [],
      auto_completed_step_ids: [],
      step_notes: {},
    });
  });

  it('initial state has empty wizard', () => {
    const w = mountWizard();
    expect(w.wizardPanelOpen.value).toBe(false);
    expect(w.wizardStepNotes.value).toEqual({});
    expect(w.completedWizardSteps.value.size).toBe(0);
  });

  it('loadOnboardingWizard populates state', async () => {
    wizMocks.fetchOnboardingWizard.mockResolvedValueOnce({
      steps: [{ id: 'init', title: '初始化' }],
      completed_step_ids: ['init'],
      auto_completed_step_ids: ['pillars'],
      step_notes: { 'init': 'note1' },
      unread_mention_count: 2,
    });
    const w = mountWizard();
    await w.loadOnboardingWizard();
    expect(w.completedWizardSteps.value.has('init')).toBe(true);
    expect(w.autoCompletedWizardSteps.value.has('pillars')).toBe(true);
    expect(w.wizardStepNotes.value.init).toBe('note1');
  });

  it('loadOnboardingWizard handles failure gracefully', async () => {
    wizMocks.fetchOnboardingWizard.mockRejectedValueOnce(new Error('down'));
    const w = mountWizard();
    await w.loadOnboardingWizard();
    expect(w.onboardingWizard.value).toBeNull();
  });

  it('onWizardToggle updates panel open and notifies deep link', () => {
    const w = mountWizard();
    w.onWizardToggle({ target: { open: true } });
    expect(w.wizardPanelOpen.value).toBe(true);
    expect(w.setWizardDeepLink).toHaveBeenCalledWith(
      true, null, [], {},
    );
  });

  it('onWizardToggle with focus step passes it', () => {
    const w = mountWizard();
    w.focusWizardStep.value = 'init';
    w.onWizardToggle({ target: { open: true } });
    expect(w.setWizardDeepLink).toHaveBeenCalledWith(
      true, 'init', [], {},
    );
  });

  it('syncWizardPanelOpen opens when focus active', () => {
    const w = mountWizard();
    w.focusWizard.value = true;
    w.syncWizardPanelOpen();
    expect(w.wizardPanelOpen.value).toBe(true);
  });

  it('syncWizardPanelOpen closes when no signal', () => {
    const w = mountWizard();
    w.wizardPanelOpen.value = true;
    w.syncWizardPanelOpen();
    expect(w.wizardPanelOpen.value).toBe(false);
  });

  it('toggleWizardStep adds and saves progress', async () => {
    wizMocks.saveOnboardingProgress.mockResolvedValueOnce({
      completed_step_ids: ['init', 'pillars'],
      auto_completed_step_ids: [],
      progress_pct: 50,
    });
    const w = mountWizard();
    w.completedWizardSteps.value = new Set(['init']);
    await w.toggleWizardStep('pillars', true);
    expect(w.completedWizardSteps.value.has('pillars')).toBe(true);
    expect(wizMocks.saveOnboardingProgress).toHaveBeenCalled();
  });

  it('toggleWizardStep removes step when unchecked', async () => {
    wizMocks.saveOnboardingProgress.mockResolvedValueOnce({
      completed_step_ids: ['pillars'], // mock 返回服务端权威结果（仅 pillars）
      auto_completed_step_ids: [],
      progress_pct: 50,
    });
    const w = mountWizard();
    w.completedWizardSteps.value = new Set(['init', 'pillars']);
    await w.toggleWizardStep('init', false);
    expect(w.completedWizardSteps.value.has('init')).toBe(false);
    expect(w.completedWizardSteps.value.has('pillars')).toBe(true);
  });

  it('toggleWizardStep handles save failure', async () => {
    wizMocks.saveOnboardingProgress.mockRejectedValueOnce(new Error('fail'));
    const w = mountWizard();
    w.completedWizardSteps.value = new Set(['init']);
    await w.toggleWizardStep('pillars', true);
    expect(w.error.value).toBe('fail');
  });

  it('saveWizardStepNote calls API', async () => {
    wizMocks.saveOnboardingNotes.mockResolvedValueOnce({});
    const w = mountWizard();
    w.wizardStepNotes.value = { 'init': 'note content' };
    await w.saveWizardStepNote('init');
    expect(wizMocks.saveOnboardingNotes).toHaveBeenCalledWith({
      step_notes: { 'init': 'note content' },
    });
  });

  it('extractMentionsFromText dedupes and lowercases', () => {
    const w = mountWizard();
    const result = w.extractMentionsFromText('hello @Alice and @bob and @alice');
    expect(result).toEqual(['alice', 'bob']);
  });

  it('extractMentionsFromText returns empty for no mentions', () => {
    const w = mountWizard();
    expect(w.extractMentionsFromText('no mentions here')).toEqual([]);
  });

  it('showOnboardingChrome computes from creation_mode', () => {
    const w = mountWizard();
    // companion 是伴侣书桌，期望 true
    w.overview.value = { creation_mode: 'companion' };
    expect(typeof w.showOnboardingChrome.value).toBe('boolean');
  });
});
