/**
 * useOnboardingNotifications 子模块独立测试
 *
 * Phase 39: 为 Phase 19.7 useOnboardingNotifications 子模块添加专门测试。
 * 重点测试：通知/digest/webhook/email 配置。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';

const onbMocks = vi.hoisted(() => ({
  fetchOnboardingNotifications: vi.fn(),
  buildOnboardingNotificationDigest: vi.fn(),
  fetchDigestSchedule: vi.fn(),
  saveDigestSchedule: vi.fn(),
  dispatchDigestNow: vi.fn(),
  processDigestRetries: vi.fn(),
  replayDigestDeadLetter: vi.fn(),
  fetchDigestRetryQueue: vi.fn(),
  fetchDigestDeadLetter: vi.fn(),
  fetchDigestStats: vi.fn(),
  fetchOnboardingWebhookConfig: vi.fn(),
  saveOnboardingWebhookConfig: vi.fn(),
  fetchOnboardingEmailConfig: vi.fn(),
  saveOnboardingEmailConfig: vi.fn(),
  ackOnboardingNotifications: vi.fn(),
}));

vi.mock('@/api/onboarding', () => {
  const m = onbMocks;
  return {
    fetchOnboardingNotifications: (...args: unknown[]) => m.fetchOnboardingNotifications(...args),
    buildOnboardingNotificationDigest: (...args: unknown[]) => m.buildOnboardingNotificationDigest(...args),
    fetchDigestSchedule: (...args: unknown[]) => m.fetchDigestSchedule(...args),
    saveDigestSchedule: (...args: unknown[]) => m.saveDigestSchedule(...args),
    dispatchDigestNow: (...args: unknown[]) => m.dispatchDigestNow(...args),
    processDigestRetries: (...args: unknown[]) => m.processDigestRetries(...args),
    replayDigestDeadLetter: (...args: unknown[]) => m.replayDigestDeadLetter(...args),
    fetchDigestRetryQueue: (...args: unknown[]) => m.fetchDigestRetryQueue(...args),
    fetchDigestDeadLetter: (...args: unknown[]) => m.fetchDigestDeadLetter(...args),
    fetchDigestStats: (...args: unknown[]) => m.fetchDigestStats(...args),
    fetchOnboardingWebhookConfig: (...args: unknown[]) => m.fetchOnboardingWebhookConfig(...args),
    saveOnboardingWebhookConfig: (...args: unknown[]) => m.saveOnboardingWebhookConfig(...args),
    fetchOnboardingEmailConfig: (...args: unknown[]) => m.fetchOnboardingEmailConfig(...args),
    saveOnboardingEmailConfig: (...args: unknown[]) => m.saveOnboardingEmailConfig(...args),
    ackOnboardingNotifications: (...args: unknown[]) => m.ackOnboardingNotifications(...args),
  };
});

import { useOnboardingNotifications } from '../../src/composables/useCreatorOnboarding/useOnboardingNotifications';

function mountOnb() {
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const handleSaveError = vi.fn();
  const wizardUnreadMentions = ref(0);
  const onboardingWizardUnreadFallback = ref<number | undefined>(undefined);
  const ctx = useOnboardingNotifications({
    error, saveMessage, handleSaveError,
    wizardUnreadMentions, onboardingWizardUnreadFallback,
  });
  return { ...ctx, error, saveMessage, handleSaveError };
}

describe('useOnboardingNotifications', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    onbMocks.fetchOnboardingNotifications.mockResolvedValue({
      notifications: [], handles: [], unread: 0,
    });
    onbMocks.buildOnboardingNotificationDigest.mockResolvedValue({
      unread: 0, group_count: 0, groups: [],
    });
    onbMocks.fetchDigestSchedule.mockResolvedValue({
      enabled: false, interval_hours: 24,
    });
    onbMocks.fetchDigestStats.mockResolvedValue({ sent_total: 0, failed_total: 0 });
    onbMocks.fetchDigestRetryQueue.mockResolvedValue({ item_count: 0, items: [] });
    onbMocks.fetchDigestDeadLetter.mockResolvedValue({ item_count: 0, items: [] });
    onbMocks.fetchOnboardingWebhookConfig.mockResolvedValue({ url: '', enabled: false });
    onbMocks.fetchOnboardingEmailConfig.mockResolvedValue({ to_addresses: [], smtp_host: '', enabled: false });
  });

  it('initial state has defaults', () => {
    const o = mountOnb();
    expect(o.wizardNotifications.value).toEqual([]);
    expect(o.wizardUnreadMentions.value).toBe(0);
    expect(o.wizardNotificationHandleFilter.value).toBe('');
    expect(o.wizardDigestScheduleEnabled.value).toBe(false);
    expect(o.wizardDigestScheduleHours.value).toBe(24);
  });

  it('loadWizardNotifications populates state', async () => {
    onbMocks.fetchOnboardingNotifications.mockResolvedValueOnce({
      notifications: [{ id: 'n1', text: 'hello' }],
      handles: ['@alice'],
      unread: 3,
    });
    const o = mountOnb();
    await o.loadWizardNotifications();
    expect(o.wizardNotifications.value).toHaveLength(1);
    expect(o.wizardNotificationHandles.value).toEqual(['@alice']);
    expect(o.wizardUnreadMentions.value).toBe(3);
  });

  it('loadWizardNotifications handles failure', async () => {
    onbMocks.fetchOnboardingNotifications.mockRejectedValueOnce(new Error('down'));
    const o = mountOnb();
    await o.loadWizardNotifications();
    expect(o.wizardNotifications.value).toEqual([]);
  });

  it('saveWizardDigestSchedule posts and saves message', async () => {
    onbMocks.saveDigestSchedule.mockResolvedValueOnce({});
    const o = mountOnb();
    o.wizardDigestScheduleEnabled.value = true;
    o.wizardDigestScheduleHours.value = 48;
    await o.saveWizardDigestSchedule();
    expect(onbMocks.saveDigestSchedule).toHaveBeenCalled();
    expect(o.saveMessage.value).toContain('digest');
  });

  it('saveWizardDigestSchedule handles failure via handleSaveError', async () => {
    onbMocks.saveDigestSchedule.mockRejectedValueOnce(new Error('fail'));
    const o = mountOnb();
    await o.saveWizardDigestSchedule();
    expect(o.handleSaveError).toHaveBeenCalled();
  });

  it('dispatchWizardDigest updates message on success', async () => {
    onbMocks.dispatchDigestNow.mockResolvedValueOnce({ sent: true, reason: '' });
    const o = mountOnb();
    await o.dispatchWizardDigest();
    expect(o.saveMessage.value).toContain('已发送');
  });

  it('dispatchWizardDigest reports skip reason', async () => {
    onbMocks.dispatchDigestNow.mockResolvedValueOnce({ sent: false, reason: 'quiet hours' });
    const o = mountOnb();
    await o.dispatchWizardDigest();
    expect(o.saveMessage.value).toContain('quiet hours');
  });

  it('processWizardDigestRetries reports retry count', async () => {
    onbMocks.processDigestRetries.mockResolvedValueOnce({ retried: 5, remaining: 2 });
    const o = mountOnb();
    await o.processWizardDigestRetries();
    expect(o.saveMessage.value).toContain('已重试 5');
    expect(o.saveMessage.value).toContain('剩余 2');
  });

  it('replayWizardDigestDeadLetter reports channel', async () => {
    onbMocks.replayDigestDeadLetter.mockResolvedValueOnce({ channel: 'email' });
    const o = mountOnb();
    await o.replayWizardDigestDeadLetter();
    expect(o.saveMessage.value).toContain('email');
  });

  it('loadWizardWebhook populates state', async () => {
    onbMocks.fetchOnboardingWebhookConfig.mockResolvedValueOnce({
      url: 'https://hook.example.com', enabled: true, signing_secret: 'secret123',
    });
    const o = mountOnb();
    await o.loadWizardWebhook();
    expect(o.wizardWebhookUrl.value).toBe('https://hook.example.com');
    expect(o.wizardWebhookEnabled.value).toBe(true);
    expect(o.wizardWebhookSigningSecret.value).toBe('secret123');
  });

  it('loadWizardWebhook handles failure', async () => {
    onbMocks.fetchOnboardingWebhookConfig.mockRejectedValueOnce(new Error('down'));
    const o = mountOnb();
    await o.loadWizardWebhook();
    expect(o.wizardWebhookUrl.value).toBe('');
    expect(o.wizardWebhookEnabled.value).toBe(false);
  });

  it('saveWizardWebhook posts and saves message', async () => {
    onbMocks.saveOnboardingWebhookConfig.mockResolvedValueOnce({});
    const o = mountOnb();
    o.wizardWebhookUrl.value = 'https://hook.example.com';
    await o.saveWizardWebhook();
    expect(o.saveMessage.value).toContain('Webhook');
  });

  it('loadWizardEmail populates state', async () => {
    onbMocks.fetchOnboardingEmailConfig.mockResolvedValueOnce({
      to_addresses: ['test@example.com', 'admin@example.com'],
      smtp_host: 'smtp.example.com',
      enabled: true,
    });
    const o = mountOnb();
    await o.loadWizardEmail();
    expect(o.wizardEmailTo.value).toBe('test@example.com, admin@example.com');
    expect(o.wizardEmailSmtpHost.value).toBe('smtp.example.com');
    expect(o.wizardEmailEnabled.value).toBe(true);
  });

  it('saveWizardEmail posts and saves message', async () => {
    onbMocks.saveOnboardingEmailConfig.mockResolvedValueOnce({});
    const o = mountOnb();
    o.wizardEmailTo.value = 'a@b.com';
    await o.saveWizardEmail();
    expect(onbMocks.saveOnboardingEmailConfig).toHaveBeenCalled();
    expect(o.saveMessage.value).toContain('邮件');
  });

  it('ackWizardNotifications reloads and shows count', async () => {
    onbMocks.ackOnboardingNotifications.mockResolvedValueOnce({ unread: 0, acked: 5 });
    const o = mountOnb();
    await o.ackWizardNotifications();
    expect(o.saveMessage.value).toContain('5');
    expect(o.saveMessage.value).toContain('已读');
  });

  it('ackWizardNotifications handles failure', async () => {
    onbMocks.ackOnboardingNotifications.mockRejectedValueOnce(new Error('fail'));
    const o = mountOnb();
    await o.ackWizardNotifications();
    expect(o.handleSaveError).toHaveBeenCalled();
  });
});
