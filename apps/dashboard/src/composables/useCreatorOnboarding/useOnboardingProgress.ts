/**
 * useOnboardingProgress — 模式链接/进度状态/mention 解析
 *
 * Phase 19 Task 7 占位：useCreatorOnboarding.js 555 行拆为 3 子模块之一。
 * 负责: onboardingProgress + wizardMentionsForStep + onboardingModesForStep +
 *       isOnboardingStepLinkedToCurrentMode + linkModeToOnboardingStep。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { ComputedRef, Ref } from 'vue';

export interface OnboardingProgressDeps {
  // 暂未使用（待后续会话填充）
}

export interface OnboardingProgressReturn {
  onboardingProgress: ComputedRef<{ completed: number; total: number; percent: number }>;
  wizardMentionsForStep: (stepId: string) => Array<{ id: string; name: string }>;
  onboardingModesForStep: (stepId: string) => string[];
  isOnboardingStepLinkedToCurrentMode: (stepId: string) => boolean;
  linkModeToOnboardingStep: (mode: string) => Promise<void>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useOnboardingProgress(_deps: OnboardingProgressDeps): OnboardingProgressReturn {
  throw new Error('useOnboardingProgress: not yet implemented (Phase 19 Task 7.2)');
}