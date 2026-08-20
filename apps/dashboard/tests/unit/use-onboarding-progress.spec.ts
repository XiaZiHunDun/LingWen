/**
 * useOnboardingProgress 子模块独立测试
 *
 * Phase 39: 为 Phase 19.7 useOnboardingProgress 子模块添加专门测试。
 * 重点测试：mention 解析 + 模式链接 + 步骤查询。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed, ComputedRef } from 'vue';

import { useOnboardingProgress } from '../../src/composables/useCreatorOnboarding/useOnboardingProgress';

function mountProgress(uiProfileOverrides: Record<string, unknown> = {}) {
  const uiProfile = ref<Record<string, unknown>>({
    creation_mode_onboarding_step_link: true,
    ...uiProfileOverrides,
  });
  const overview = ref<Record<string, unknown> | null>({ creation_mode: 'companion' });
  const saveMessage = ref('');
  const onboardingWizard = ref<Record<string, unknown> | null>(null);
  const wizardStepNotes = ref<Record<string, string>>({});
  const extractMentionsFromText = (text: string): string[] => {
    const found: string[] = [];
    const re = /@([a-zA-Z][a-zA-Z0-9_-]{0,31})/g;
    let m = re.exec(String(text || ''));
    while (m) {
      const handle = m[1].toLowerCase();
      if (!found.includes(handle)) found.push(handle);
      m = re.exec(String(text || ''));
    }
    return found;
  };
  const setWizardDeepLink = vi.fn();
  const focusWizardStepFromUrl = vi.fn(async () => {});

  const ctx = useOnboardingProgress({
    uiProfile: uiProfile as unknown as ComputedRef<Record<string, unknown>>,
    overview, saveMessage,
    onboardingWizard, wizardStepNotes,
    extractMentionsFromText, setWizardDeepLink, focusWizardStepFromUrl,
    } as unknown as Parameters<typeof useOnboardingProgress>[0]);
  return { ...ctx, overview, onboardingWizard, wizardStepNotes, saveMessage, setWizardDeepLink, focusWizardStepFromUrl, uiProfile };
}

describe('useOnboardingProgress', () => {
  beforeEach(() => vi.clearAllMocks());

  it('initial state: wizardMentionsForStep returns empty when no data', () => {
    const p = mountProgress();
    expect(p.wizardMentionsForStep('init')).toEqual([]);
  });

  it('wizardMentionsForStep returns API mentions when available', () => {
    const p = mountProgress();
    p.onboardingWizard.value = {
      step_mentions: { 'init': ['@alice', '@bob'] },
    };
    // API 返回值原样使用（包含 @ 前缀）
    expect(p.wizardMentionsForStep('init')).toEqual(['@alice', '@bob']);
  });

  it('wizardMentionsForStep falls back to text extraction when API empty', () => {
    const p = mountProgress();
    p.wizardStepNotes.value = { 'init': 'hello @alice and @bob' };
    expect(p.wizardMentionsForStep('init')).toEqual(['alice', 'bob']);
  });

  it('wizardMentionsForStep prefers API over text when API has data', () => {
    const p = mountProgress();
    p.onboardingWizard.value = { step_mentions: { 'init': ['@alice'] } };
    p.wizardStepNotes.value = { 'init': 'hello @bob' };
    // API 有数据时优先使用 API，不调用 text extraction
    expect(p.wizardMentionsForStep('init')).toEqual(['@alice']);
  });

  it('wizardMentionsForStep returns empty for missing stepId', () => {
    const p = mountProgress();
    p.wizardStepNotes.value = { 'init': '@alice' };
    expect(p.wizardMentionsForStep('nonexistent')).toEqual([]);
  });

  it('onboardingModesForStep returns empty when link disabled', () => {
    const p = mountProgress({ creation_mode_onboarding_step_link: false });
    expect(p.onboardingModesForStep('init')).toEqual([]);
  });

  it('onboardingModesForStep returns modes for given step', () => {
    const p = mountProgress();
    const modes = p.onboardingModesForStep('init');
    expect(modes.length).toBeGreaterThan(0);
    expect(modes.find((m) => m.mode === 'companion')).toBeDefined();
  });

  it('isOnboardingStepLinkedToCurrentMode false when link disabled', () => {
    const p = mountProgress({ creation_mode_onboarding_step_link: false });
    expect(p.isOnboardingStepLinkedToCurrentMode('init')).toBe(false);
  });

  it('isOnboardingStepLinkedToCurrentMode true when step in mode', () => {
    const p = mountProgress();
    // companion 模式包含 init
    expect(p.isOnboardingStepLinkedToCurrentMode('init')).toBe(true);
  });

  it('isOnboardingStepLinkedToCurrentMode false when step not in mode', () => {
    const p = mountProgress();
    expect(p.isOnboardingStepLinkedToCurrentMode('nonexistent-step')).toBe(false);
  });

  it('linkModeToOnboardingStep no-ops when link disabled', async () => {
    const p = mountProgress({ creation_mode_onboarding_step_link: false });
    await p.linkModeToOnboardingStep('companion');
    expect(p.setWizardDeepLink).not.toHaveBeenCalled();
  });

  it('linkModeToOnboardingStep no-ops when mode empty', async () => {
    const p = mountProgress();
    await p.linkModeToOnboardingStep('');
    expect(p.setWizardDeepLink).not.toHaveBeenCalled();
  });

  it('linkModeToOnboardingStep opens panel and saves message', async () => {
    const p = mountProgress();
    await p.linkModeToOnboardingStep('companion');
    expect(p.setWizardDeepLink).toHaveBeenCalledWith(true, 'write');
    expect(p.focusWizardStepFromUrl).toHaveBeenCalled();
    expect(p.saveMessage.value).toContain('联动');
  });
});
