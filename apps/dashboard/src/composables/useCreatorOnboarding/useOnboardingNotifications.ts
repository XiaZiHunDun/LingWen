/**
 * useOnboardingNotifications — 通知/digest/webhook/email
 *
 * Phase 19 Task 7：从 useCreatorOnboarding.js 拆出（完整实现）。
 * 负责: wizardNotifications + loadWizardNotifications + ackWizardNotifications +
 *       loadWizardDigestSchedule + saveWizardDigestSchedule +
 *       dispatchWizardDigest + processWizardDigestRetries + replayWizardDigestDeadLetter +
 *       loadWizardWebhook + saveWizardWebhook + loadWizardEmail + saveWizardEmail。
 *
 * 注: wizardUnreadMentions 是与 useWizardSteps 共享状态，通过 deps 传入。
 */
import { ref } from 'vue';
import type { Ref } from 'vue';
import {
  fetchOnboardingNotifications,
  buildOnboardingNotificationDigest,
  fetchDigestSchedule,
  saveDigestSchedule,
  dispatchDigestNow,
  fetchDigestRetryQueue,
  fetchDigestStats,
  processDigestRetries,
  fetchDigestDeadLetter,
  replayDigestDeadLetter,
  ackOnboardingNotifications,
  fetchOnboardingWebhookConfig,
  saveOnboardingWebhookConfig,
  fetchOnboardingEmailConfig,
  saveOnboardingEmailConfig,
} from '@/api/onboarding';

interface NotificationDigest {
  unread: number;
  group_count: number;
  groups: Array<Record<string, unknown>>;
}

interface DigestSchedule {
  enabled: boolean;
  interval_hours: number;
  quiet_hours_start?: number | null;
  quiet_hours_end?: number | null;
  handle_channels?: Record<string, string[]>;
  handle_quiet_hours?: Record<string, [number, number]>;
}

interface DigestQueue {
  item_count: number;
  items: Array<Record<string, unknown>>;
}

interface DigestStats {
  sent_total: number;
  failed_total: number;
}

interface WebhookConfig {
  url: string;
  enabled: boolean;
  signing_secret?: string;
}

interface EmailConfig {
  to_addresses: string[];
  smtp_host?: string;
  enabled: boolean;
}

export interface OnboardingNotificationsDeps {
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  handleSaveError: (err: unknown) => void;
  wizardUnreadMentions: Ref<number>;
  onboardingWizardUnreadFallback: Ref<number | undefined>;
}

export interface OnboardingNotificationsReturn {
  wizardNotifications: Ref<Array<Record<string, unknown>>>;
  wizardUnreadMentions: Ref<number>;
  wizardNotificationHandleFilter: Ref<string>;
  wizardNotificationHandles: Ref<string[]>;
  wizardWebhookUrl: Ref<string>;
  wizardWebhookEnabled: Ref<boolean>;
  wizardEmailTo: Ref<string>;
  wizardEmailSmtpHost: Ref<string>;
  wizardEmailEnabled: Ref<boolean>;
  wizardNotificationDigest: Ref<NotificationDigest>;
  wizardDigestScheduleEnabled: Ref<boolean>;
  wizardDigestScheduleHours: Ref<number>;
  wizardDigestQuietStart: Ref<number | null>;
  wizardDigestQuietEnd: Ref<number | null>;
  wizardDigestHandleChannelsJson: Ref<string>;
  wizardDigestHandleQuietJson: Ref<string>;
  wizardDigestStats: Ref<DigestStats>;
  wizardDigestDeadLetter: Ref<DigestQueue>;
  wizardDigestRetryQueue: Ref<DigestQueue>;
  wizardWebhookSigningSecret: Ref<string>;
  loadWizardNotifications: () => Promise<void>;
  saveWizardDigestSchedule: () => Promise<void>;
  processWizardDigestRetries: () => Promise<void>;
  replayWizardDigestDeadLetter: () => Promise<void>;
  dispatchWizardDigest: () => Promise<void>;
  loadWizardWebhook: () => Promise<void>;
  saveWizardWebhook: () => Promise<void>;
  loadWizardEmail: () => Promise<void>;
  saveWizardEmail: () => Promise<void>;
  ackWizardNotifications: () => Promise<void>;
}

export function useOnboardingNotifications(deps: OnboardingNotificationsDeps): OnboardingNotificationsReturn {
  const { saveMessage, handleSaveError, wizardUnreadMentions, onboardingWizardUnreadFallback } = deps;

  const wizardNotifications = ref<Array<Record<string, unknown>>>([]);
  const wizardNotificationHandleFilter = ref('');
  const wizardNotificationHandles = ref<string[]>([]);
  const wizardWebhookUrl = ref('');
  const wizardWebhookEnabled = ref(false);
  const wizardEmailTo = ref('');
  const wizardEmailSmtpHost = ref('');
  const wizardEmailEnabled = ref(false);
  const wizardNotificationDigest = ref<NotificationDigest>({ unread: 0, group_count: 0, groups: [] });
  const wizardDigestScheduleEnabled = ref(false);
  const wizardDigestScheduleHours = ref(24);
  const wizardDigestQuietStart = ref<number | null>(null);
  const wizardDigestQuietEnd = ref<number | null>(null);
  const wizardDigestHandleChannelsJson = ref('');
  const wizardDigestHandleQuietJson = ref('');
  const wizardDigestStats = ref<DigestStats>({ sent_total: 0, failed_total: 0 });
  const wizardDigestDeadLetter = ref<DigestQueue>({ item_count: 0, items: [] });
  const wizardDigestRetryQueue = ref<DigestQueue>({ item_count: 0, items: [] });
  const wizardWebhookSigningSecret = ref('');

  async function loadWizardNotifications(): Promise<void> {
    try {
      // Phase 126 v16.2.4 T6: typed wrapper `fetchOnboardingNotifications` /
      // `buildOnboardingNotificationDigest` don't yet forward `handle` query
      // param (Phase 127+ will add optional query support via core.js). Until
      // then we pass handle to backend through URL state (router query) which
      // matches the v16.2.3 shim behaviour (handle dropped identically).
      const data = await fetchOnboardingNotifications() as unknown as {
        notifications: Array<Record<string, unknown>>;
        handles: string[];
        unread?: number;
      };
      wizardNotifications.value = data.notifications || [];
      wizardNotificationHandles.value = data.handles || [];
      wizardUnreadMentions.value = data.unread ?? wizardNotifications.value.filter((n) => !n.read).length;
      const digest = await buildOnboardingNotificationDigest() as unknown as NotificationDigest;
      wizardNotificationDigest.value = digest;
      await loadWizardDigestSchedule();
      await loadWizardWebhook();
      await loadWizardEmail();
    } catch {
      wizardNotifications.value = [];
      wizardNotificationHandles.value = [];
      wizardUnreadMentions.value = onboardingWizardUnreadFallback.value || 0;
      wizardNotificationDigest.value = { unread: 0, group_count: 0, groups: [] };
      wizardDigestScheduleEnabled.value = false;
      wizardDigestScheduleHours.value = 24;
    }
  }

  async function loadWizardDigestSchedule(): Promise<void> {
    try {
      const data = await fetchDigestSchedule() as DigestSchedule;
      wizardDigestScheduleEnabled.value = Boolean(data.enabled);
      wizardDigestScheduleHours.value = data.interval_hours || 24;
      wizardDigestQuietStart.value = data.quiet_hours_start ?? null;
      wizardDigestQuietEnd.value = data.quiet_hours_end ?? null;
      wizardDigestHandleChannelsJson.value = JSON.stringify(data.handle_channels || {});
      wizardDigestHandleQuietJson.value = JSON.stringify(data.handle_quiet_hours || {});
      const stats = await fetchDigestStats() as DigestStats;
      wizardDigestStats.value = stats;
      const retry = await fetchDigestRetryQueue() as unknown as DigestQueue;
      wizardDigestRetryQueue.value = retry;
      const deadLetter = await fetchDigestDeadLetter() as unknown as DigestQueue;
      wizardDigestDeadLetter.value = deadLetter;
    } catch {
      wizardDigestScheduleEnabled.value = false;
      wizardDigestScheduleHours.value = 24;
      wizardDigestQuietStart.value = null;
      wizardDigestQuietEnd.value = null;
      wizardDigestRetryQueue.value = { item_count: 0, items: [] };
    }
  }

  async function saveWizardDigestSchedule(): Promise<void> {
    try {
      let handleChannels: Record<string, unknown> = {};
      let handleQuietHours: Record<string, unknown> = {};
      if (wizardDigestHandleChannelsJson.value.trim()) {
        handleChannels = JSON.parse(wizardDigestHandleChannelsJson.value);
      }
      if (wizardDigestHandleQuietJson.value.trim()) {
        handleQuietHours = JSON.parse(wizardDigestHandleQuietJson.value);
      }
      await saveDigestSchedule({
        enabled: wizardDigestScheduleEnabled.value,
        interval_hours: wizardDigestScheduleHours.value,
        channels: ['webhook', 'email'],
        handle_channels: handleChannels,
        handle_quiet_hours: handleQuietHours,
        quiet_hours_start: wizardDigestQuietStart.value,
        quiet_hours_end: wizardDigestQuietEnd.value,
      });
      saveMessage.value = '已保存 digest 定时';
      await loadWizardDigestSchedule();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function processWizardDigestRetries(): Promise<void> {
    try {
      const result = await processDigestRetries() as { retried: number; remaining: number };
      saveMessage.value = `已重试 ${result.retried} 条，剩余 ${result.remaining}`;
      await loadWizardDigestSchedule();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function replayWizardDigestDeadLetter(): Promise<void> {
    try {
      const result = await replayDigestDeadLetter({ index: 0 }) as { channel?: string };
      saveMessage.value = `已重放死信（${result.channel || 'unknown'}）`;
      await loadWizardDigestSchedule();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function dispatchWizardDigest(): Promise<void> {
    try {
      const result = await dispatchDigestNow(true) as { sent: boolean; reason?: string };
      saveMessage.value = result.sent ? '已发送 digest' : `跳过：${result.reason || '未知'}`;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function loadWizardWebhook(): Promise<void> {
    try {
      const data = await fetchOnboardingWebhookConfig() as WebhookConfig;
      wizardWebhookUrl.value = data.url || '';
      wizardWebhookEnabled.value = Boolean(data.enabled);
      wizardWebhookSigningSecret.value = data.signing_secret || '';
    } catch {
      wizardWebhookUrl.value = '';
      wizardWebhookEnabled.value = false;
    }
  }

  async function saveWizardWebhook(): Promise<void> {
    try {
      await saveOnboardingWebhookConfig({
        url: wizardWebhookUrl.value.trim(),
        enabled: wizardWebhookEnabled.value,
        mention_handles: wizardNotificationHandles.value,
        signing_secret: wizardWebhookSigningSecret.value.trim(),
      });
      saveMessage.value = '已保存通知 Webhook';
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function loadWizardEmail(): Promise<void> {
    try {
      const data = await fetchOnboardingEmailConfig() as EmailConfig;
      wizardEmailTo.value = (data.to_addresses || []).join(', ');
      wizardEmailSmtpHost.value = data.smtp_host || '';
      wizardEmailEnabled.value = Boolean(data.enabled);
    } catch {
      wizardEmailTo.value = '';
      wizardEmailSmtpHost.value = '';
      wizardEmailEnabled.value = false;
    }
  }

  async function saveWizardEmail(): Promise<void> {
    try {
      const toAddresses = wizardEmailTo.value
        .split(',')
        .map((addr) => addr.trim())
        .filter(Boolean);
      await saveOnboardingEmailConfig({
        enabled: wizardEmailEnabled.value,
        to_addresses: toAddresses,
        mention_handles: wizardNotificationHandles.value,
        smtp_host: wizardEmailSmtpHost.value.trim(),
        smtp_port: 587,
        smtp_use_tls: true,
        from_address: toAddresses[0] || '',
      });
      saveMessage.value = '已保存通知邮件';
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function ackWizardNotifications(): Promise<void> {
    try {
      const result = await ackOnboardingNotifications({
        all_notifications: true,
        handle: wizardNotificationHandleFilter.value || undefined,
      }) as { unread?: number; acked: number };
      wizardUnreadMentions.value = result.unread ?? 0;
      await loadWizardNotifications();
      saveMessage.value = `已标记 ${result.acked} 条通知为已读`;
    } catch (e) {
      handleSaveError(e);
    }
  }

  return {
    wizardNotifications,
    wizardUnreadMentions,
    wizardNotificationHandleFilter,
    wizardNotificationHandles,
    wizardWebhookUrl,
    wizardWebhookEnabled,
    wizardEmailTo,
    wizardEmailSmtpHost,
    wizardEmailEnabled,
    wizardNotificationDigest,
    wizardDigestScheduleEnabled,
    wizardDigestScheduleHours,
    wizardDigestQuietStart,
    wizardDigestQuietEnd,
    wizardDigestHandleChannelsJson,
    wizardDigestHandleQuietJson,
    wizardDigestStats,
    wizardDigestDeadLetter,
    wizardDigestRetryQueue,
    wizardWebhookSigningSecret,
    loadWizardNotifications,
    saveWizardDigestSchedule,
    processWizardDigestRetries,
    replayWizardDigestDeadLetter,
    dispatchWizardDigest,
    loadWizardWebhook,
    saveWizardWebhook,
    loadWizardEmail,
    saveWizardEmail,
    ackWizardNotifications,
  };
}
