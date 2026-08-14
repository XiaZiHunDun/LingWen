/**
 * useOnboardingNotifications — 通知/digest/webhook/email
 *
 * Phase 19 Task 7 占位：useCreatorOnboarding.js 555 行拆为 3 子模块之一。
 * 负责: wizardNotifications + loadWizardNotifications + ackWizardNotifications +
 *       loadWizardDigestSchedule + saveWizardDigestSchedule +
 *       dispatchWizardDigest + processWizardDigestRetries + replayWizardDigestDeadLetter +
 *       loadWizardWebhook + saveWizardWebhook + loadWizardEmail + saveWizardEmail。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface OnboardingNotificationsDeps {
  // 暂未使用（待后续会话填充）
}

export interface OnboardingNotificationsReturn {
  wizardNotifications: Ref<Array<Record<string, unknown>>>;
  wizardNotificationUnread: Ref<number>;
  wizardDigestSchedule: Ref<Record<string, unknown>>;
  wizardWebhookConfig: Ref<Record<string, unknown>>;
  wizardEmailConfig: Ref<Record<string, unknown>>;
  wizardDigestDispatching: Ref<boolean>;
  loadWizardNotifications: () => Promise<void>;
  ackWizardNotifications: () => Promise<void>;
  loadWizardDigestSchedule: () => Promise<void>;
  saveWizardDigestSchedule: () => Promise<void>;
  dispatchWizardDigest: () => Promise<void>;
  processWizardDigestRetries: () => Promise<void>;
  replayWizardDigestDeadLetter: () => Promise<void>;
  loadWizardWebhook: () => Promise<void>;
  saveWizardWebhook: () => Promise<void>;
  loadWizardEmail: () => Promise<void>;
  saveWizardEmail: () => Promise<void>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useOnboardingNotifications(_deps: OnboardingNotificationsDeps): OnboardingNotificationsReturn {
  throw new Error('useOnboardingNotifications: not yet implemented (Phase 19 Task 7.3)');
}