/**
 * useCreatorOnboarding — 入门向导逻辑（从 CreatorPage 抽出）
 *
 * Phase 19 Task 7 完成版：抽出全部 3 个 .ts 子模块，本主 hook 改为组合 facade。
 * 下游 API（panelContext shape）保持完全兼容。
 *
 * 子模块：
 * - useWizardSteps            (向导步骤 + 分享/链接 + note/复选)
 * - useOnboardingProgress     (模式链接/进度状态/mention 解析)
 * - useOnboardingNotifications (通知/digest/webhook/email)
 *
 * 共享状态:
 * - wizardUnreadMentions: 由 notifications 拥有，steps 读取（panel 自动展开）
 * - onboardingWizard: 由 steps 拥有，progress 读取（mention 解析）
 * - wizardStepNotes: 由 steps 拥有，progress 读取（本地 mention 提取）
 * - wizardPanelOpen: 由 steps 拥有，main hook 在 linkModeToOnboardingStep 中写入
 */
import { computed, ref } from 'vue';
import {
  useWizardSteps,
  useOnboardingProgress,
  useOnboardingNotifications,
} from './useCreatorOnboarding/index.ts';

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   handleSaveError: (err: unknown) => void,
 *   focusWizard: import('vue').Ref<boolean>,
 *   focusWizardStep: import('vue').Ref<string|null>,
 *   focusWizardDone: import('vue').Ref<string[]>,
 *   focusWizardNotes: import('vue').Ref<Record<string, string>>,
 *   setWizardDeepLink: Function,
 *   buildWizardShareUrl: Function,
 * } deps
 */
export function useCreatorOnboarding(deps) {
  const {
    uiProfile, overview, error, saveMessage, handleSaveError,
    focusWizard, focusWizardStep, focusWizardDone, focusWizardNotes,
    setWizardDeepLink, buildWizardShareUrl,
  } = deps;

  // --- 共享状态: wizardUnreadMentions（notifications 拥有，steps 读取）---
  const wizardUnreadMentions = ref(0);
  // fallback when notifications load fails: use wizard.unread_mention_count
  const onboardingWizardUnreadFallback = computed(() => undefined);

  // --- 1) Notifications 子模块（先建，提供 loadWizardNotifications 给 steps）---
  const notifications = useOnboardingNotifications({
    error,
    saveMessage,
    handleSaveError,
    wizardUnreadMentions,
    onboardingWizardUnreadFallback,
  });

  // --- 2) WizardSteps 子模块（依赖 notifications.loadWizardNotifications）---
  const steps = useWizardSteps({
    uiProfile,
    overview,
    error,
    focusWizard,
    focusWizardStep,
    focusWizardDone,
    focusWizardNotes,
    wizardUnreadMentions,
    loadWizardNotifications: notifications.loadWizardNotifications,
    setWizardDeepLink,
    buildWizardShareUrl,
  });

  // --- 3) OnboardingProgress 子模块（依赖 steps state）---
  const progress = useOnboardingProgress({
    uiProfile,
    overview,
    saveMessage,
    onboardingWizard: steps.onboardingWizard,
    wizardStepNotes: steps.wizardStepNotes,
    extractMentionsFromText: steps.extractMentionsFromText,
    setWizardDeepLink,
    focusWizardStepFromUrl: steps.focusWizardStepFromUrl,
  });

  // --- linkModeToOnboardingStep 包装: progress 调用 + 设置 wizardPanelOpen ---
  async function linkModeToOnboardingStep(mode) {
    if (!uiProfile.value.creation_mode_onboarding_step_link || !mode) return;
    // 主动展开向导面板（progress 模块只能通过 setWizardDeepLink 间接驱动）
    steps.wizardPanelOpen.value = true;
    await progress.linkModeToOnboardingStep(mode);
  }

  const panelContext = {
    uiProfile,
    showOnboardingChrome: steps.showOnboardingChrome,
    wizardPanelRef: steps.wizardPanelRef,
    wizardPanelOpen: steps.wizardPanelOpen,
    onboardingWizard: steps.onboardingWizard,
    wizardUnreadMentions,
    wizardNotifications: notifications.wizardNotifications,
    wizardNotificationHandles: notifications.wizardNotificationHandles,
    wizardNotificationHandleFilter: notifications.wizardNotificationHandleFilter,
    wizardNotificationDigest: notifications.wizardNotificationDigest,
    wizardDigestScheduleEnabled: notifications.wizardDigestScheduleEnabled,
    wizardDigestScheduleHours: notifications.wizardDigestScheduleHours,
    wizardDigestStats: notifications.wizardDigestStats,
    wizardDigestHandleChannelsJson: notifications.wizardDigestHandleChannelsJson,
    wizardDigestHandleQuietJson: notifications.wizardDigestHandleQuietJson,
    wizardDigestQuietStart: notifications.wizardDigestQuietStart,
    wizardDigestQuietEnd: notifications.wizardDigestQuietEnd,
    wizardDigestRetryQueue: notifications.wizardDigestRetryQueue,
    wizardDigestDeadLetter: notifications.wizardDigestDeadLetter,
    wizardWebhookEnabled: notifications.wizardWebhookEnabled,
    wizardWebhookUrl: notifications.wizardWebhookUrl,
    wizardWebhookSigningSecret: notifications.wizardWebhookSigningSecret,
    wizardEmailEnabled: notifications.wizardEmailEnabled,
    wizardEmailTo: notifications.wizardEmailTo,
    wizardEmailSmtpHost: notifications.wizardEmailSmtpHost,
    completedWizardSteps: steps.completedWizardSteps,
    focusWizardStep,
    autoCompletedWizardSteps: steps.autoCompletedWizardSteps,
    wizardStepNotes: steps.wizardStepNotes,
    wizardShareMessage: steps.wizardShareMessage,
    onWizardToggle: steps.onWizardToggle,
    loadWizardNotifications: notifications.loadWizardNotifications,
    saveWizardDigestSchedule: notifications.saveWizardDigestSchedule,
    dispatchWizardDigest: notifications.dispatchWizardDigest,
    processWizardDigestRetries: notifications.processWizardDigestRetries,
    replayWizardDigestDeadLetter: notifications.replayWizardDigestDeadLetter,
    ackWizardNotifications: notifications.ackWizardNotifications,
    saveWizardWebhook: notifications.saveWizardWebhook,
    saveWizardEmail: notifications.saveWizardEmail,
    toggleWizardStep: steps.toggleWizardStep,
    saveWizardStepNote: steps.saveWizardStepNote,
    wizardMentionsForStep: progress.wizardMentionsForStep,
    onboardingModesForStep: progress.onboardingModesForStep,
    isOnboardingStepLinkedToCurrentMode: progress.isOnboardingStepLinkedToCurrentMode,
    copyWizardShareLink: steps.copyWizardShareLink,
  };

  return {
    panelContext,
    wizardEmailTo: notifications.wizardEmailTo,
    onboardingWizard: steps.onboardingWizard,
    loadOnboardingWizard: steps.loadOnboardingWizard,
    syncWizardPanelOpen: steps.syncWizardPanelOpen,
    linkModeToOnboardingStep,
  };
}