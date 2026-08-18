/**
 * useOnboardingProgress — 模式链接/进度状态/mention 解析
 *
 * Phase 19 Task 7：从 useCreatorOnboarding.js 拆出（完整实现）。
 * 负责: wizardMentionsForStep + onboardingModesForStep +
 *       isOnboardingStepLinkedToCurrentMode + linkModeToOnboardingStep。
 *
 * 注: 不持有 wizard state，通过 deps 读取 onboardingWizard + wizardStepNotes。
 *     CREATION_MODE_ONBOARDING_* 常量保留为模块内私有。
 */
import { nextTick, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';

const CREATION_MODE_ONBOARDING_STEPS: Record<string, string[]> = {
  companion: ['init', 'pillars', 'dashboard', 'write', 'check'],
  advance: ['init', 'pillars', 'dashboard', 'volume', 'batch', 'check'],
  studio: ['init', 'pillars', 'dashboard', 'volume', 'preflight', 'check'],
};

const CREATION_MODE_ONBOARDING_LABELS: Record<string, string> = {
  companion: '陪伴',
  advance: '推进',
  studio: '工作室',
};

const CREATION_MODE_ONBOARDING_FOCUS_STEP: Record<string, string> = {
  companion: 'write',
  advance: 'volume',
  studio: 'preflight',
};

interface OnboardingWizard {
  step_mentions?: Record<string, string[]>;
}

export interface OnboardingProgressDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  overview: Ref<Record<string, unknown> | null>;
  saveMessage: Ref<string>;
  onboardingWizard: Ref<OnboardingWizard | null>;
  wizardStepNotes: Ref<Record<string, string>>;
  extractMentionsFromText: (text: string) => string[];
  setWizardDeepLink: (open: boolean, step?: string | null) => void;
  focusWizardStepFromUrl: () => Promise<void>;
}

export interface OnboardingProgressReturn {
  wizardMentionsForStep: (stepId: string) => string[];
  onboardingModesForStep: (stepId: string) => Array<{ mode: string; label: string }>;
  isOnboardingStepLinkedToCurrentMode: (stepId: string) => boolean;
  linkModeToOnboardingStep: (mode: string) => Promise<void>;
}

export function useOnboardingProgress(deps: OnboardingProgressDeps): OnboardingProgressReturn {
  const {
    uiProfile,
    overview,
    saveMessage,
    onboardingWizard,
    wizardStepNotes,
    extractMentionsFromText,
    setWizardDeepLink,
    focusWizardStepFromUrl,
  } = deps;

  function wizardMentionsForStep(stepId: string): string[] {
    const fromApi = onboardingWizard.value?.step_mentions?.[stepId];
    if (fromApi?.length) return fromApi;
    return extractMentionsFromText(wizardStepNotes.value[stepId] || '');
  }

  function onboardingModesForStep(stepId: string): Array<{ mode: string; label: string }> {
    if (!(uiProfile.value as { creation_mode_onboarding_step_link?: boolean }).creation_mode_onboarding_step_link) return [];
    return Object.entries(CREATION_MODE_ONBOARDING_STEPS)
      .filter(([, steps]) => steps.includes(stepId))
      .map(([mode]) => ({ mode, label: CREATION_MODE_ONBOARDING_LABELS[mode] }));
  }

  function isOnboardingStepLinkedToCurrentMode(stepId: string): boolean {
    if (!(uiProfile.value as { creation_mode_onboarding_step_link?: boolean }).creation_mode_onboarding_step_link || !overview.value) return false;
    const steps = CREATION_MODE_ONBOARDING_STEPS[(overview.value as { creation_mode?: string }).creation_mode || ''] || [];
    return steps.includes(stepId);
  }

  async function linkModeToOnboardingStep(mode: string): Promise<void> {
    if (!(uiProfile.value as { creation_mode_onboarding_step_link?: boolean }).creation_mode_onboarding_step_link || !mode) return;
    const firstStep = CREATION_MODE_ONBOARDING_FOCUS_STEP[mode];
    if (!firstStep) return;
    // 这里需要外部的 wizardPanelOpen ref — 通过 saveMessage + setWizardDeepLink 间接驱动
    setWizardDeepLink(true, firstStep);
    await nextTick();
    await focusWizardStepFromUrl();
    saveMessage.value = `已联动 ${CREATION_MODE_ONBOARDING_LABELS[mode] || mode} 向导步骤`;
  }

  return {
    wizardMentionsForStep,
    onboardingModesForStep,
    isOnboardingStepLinkedToCurrentMode,
    linkModeToOnboardingStep,
  };
}