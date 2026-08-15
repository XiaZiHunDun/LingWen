/**
 * useOnboardingNotifications 子模块独立测试
 *
 * Phase 39: 为 Phase 19.7 useOnboardingNotifications 子模块添加专门测试。
 * 重点测试：通知/digest/webhook/email 配置。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';

const onbMocks = vi.hoisted(() => ({
  fetchCreatorOnboardingNotifications: vi.fn(),
  fetchCreatorOnboardingNotificationDigest: vi.fn(),
  fetchCreatorOnboardingDigestSchedule: vi.fn(),
  saveCreatorOnboardingDigestSchedule: vi.fn(),
  dispatchCreatorOnboardingDigest: vi.fn(),
  processCreatorOnboardingDigestRetries: vi.fn(),
  replayCreatorOnboardingDigestDeadLetter: vi.fn(),
  fetchCreatorOnboardingDigestRetryQueue: vi.fn(),
  fetchCreatorOnboardingDigestDeadLetter: vi.fn(),
  fetchCreatorOnboardingDigestStats: vi.fn(),
  fetchCreatorOnboardingWebhook: vi.fn(),
  saveCreatorOnboardingWebhook: vi.fn(),
  fetchCreatorOnboardingEmail: vi.fn(),
  saveCreatorOnboardingEmail: vi.fn(),
  ackCreatorOnboardingNotifications: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => {
  const m = onbMocks;
  return {
    fetchCreatorOnboardingNotifications: (...args: unknown[]) => m.fetchCreatorOnboardingNotifications(...args),
    fetchCreatorOnboardingNotificationDigest: (...args: unknown[]) => m.fetchCreatorOnboardingNotificationDigest(...args),
    fetchCreatorOnboardingDigestSchedule: (...args: unknown[]) => m.fetchCreatorOnboardingDigestSchedule(...args),
    saveCreatorOnboardingDigestSchedule: (...args: unknown[]) => m.saveCreatorOnboardingDigestSchedule(...args),
    dispatchCreatorOnboardingDigest: (...args: unknown[]) => m.dispatchCreatorOnboardingDigest(...args),
    processCreatorOnboardingDigestRetries: (...args: unknown[]) => m.processCreatorOnboardingDigestRetries(...args),
    replayCreatorOnboardingDigestDeadLetter: (...args: unknown[]) => m.replayCreatorOnboardingDigestDeadLetter(...args),
    fetchCreatorOnboardingDigestRetryQueue: (...args: unknown[]) => m.fetchCreatorOnboardingDigestRetryQueue(...args),
    fetchCreatorOnboardingDigestDeadLetter: (...args: unknown[]) => m.fetchCreatorOnboardingDigestDeadLetter(...args),
    fetchCreatorOnboardingDigestStats: (...args: unknown[]) => m.fetchCreatorOnboardingDigestStats(...args),
    fetchCreatorOnboardingWebhook: (...args: unknown[]) => m.fetchCreatorOnboardingWebhook(...args),
    saveCreatorOnboardingWebhook: (...args: unknown[]) => m.saveCreatorOnboardingWebhook(...args),
    fetchCreatorOnboardingEmail: (...args: unknown[]) => m.fetchCreatorOnboardingEmail(...args),
    saveCreatorOnboardingEmail: (...args: unknown[]) => m.saveCreatorOnboardingEmail(...args),
    ackCreatorOnboardingNotifications: (...args: unknown[]) => m.ackCreatorOnboardingNotifications(...args),
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
    onbMocks.fetchCreatorOnboardingNotifications.mockResolvedValue({
      notifications: [], handles: [], unread: 0,
    });
    onbMocks.fetchCreatorOnboardingNotificationDigest.mockResolvedValue({
      unread: 0, group_count: 0, groups: [],
    });
    onbMocks.fetchCreatorOnboardingDigestSchedule.mockResolvedValue({
      enabled: false, interval_hours: 24,
    });
    onbMocks.fetchCreatorOnboardingDigestStats.mockResolvedValue({ sent_total: 0, failed_total: 0 });
    onbMocks.fetchCreatorOnboardingDigestRetryQueue.mockResolvedValue({ item_count: 0, items: [] });
    onbMocks.fetchCreatorOnboardingDigestDeadLetter.mockResolvedValue({ item_count: 0, items: [] });
    onbMocks.fetchCreatorOnboardingWebhook.mockResolvedValue({ url: '', enabled: false });
    onbMocks.fetchCreatorOnboardingEmail.mockResolvedValue({ to_addresses: [], smtp_host: '', enabled: false });
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
    onbMocks.fetchCreatorOnboardingNotifications.mockResolvedValueOnce({
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
    onbMocks.fetchCreatorOnboardingNotifications.mockRejectedValueOnce(new Error('down'));
    const o = mountOnb();
    await o.loadWizardNotifications();
    expect(o.wizardNotifications.value).toEqual([]);
  });

  it('saveWizardDigestSchedule posts and saves message', async () => {
    onbMocks.saveCreatorOnboardingDigestSchedule.mockResolvedValueOnce({});
    const o = mountOnb();
    o.wizardDigestScheduleEnabled.value = true;
    o.wizardDigestScheduleHours.value = 48;
    await o.saveWizardDigestSchedule();
    expect(onbMocks.saveCreatorOnboardingDigestSchedule).toHaveBeenCalled();
    expect(o.saveMessage.value).toContain('digest');
  });

  it('saveWizardDigestSchedule handles failure via handleSaveError', async () => {
    onbMocks.saveCreatorOnboardingDigestSchedule.mockRejectedValueOnce(new Error('fail'));
    const o = mountOnb();
    await o.saveWizardDigestSchedule();
    expect(o.handleSaveError).toHaveBeenCalled();
  });

  it('dispatchWizardDigest updates message on success', async () => {
    onbMocks.dispatchCreatorOnboardingDigest.mockResolvedValueOnce({ sent: true, reason: '' });
    const o = mountOnb();
    await o.dispatchWizardDigest();
    expect(o.saveMessage.value).toContain('已发送');
  });

  it('dispatchWizardDigest reports skip reason', async () => {
    onbMocks.dispatchCreatorOnboardingDigest.mockResolvedValueOnce({ sent: false, reason: 'quiet hours' });
    const o = mountOnb();
    await o.dispatchWizardDigest();
    expect(o.saveMessage.value).toContain('quiet hours');
  });

  it('processWizardDigestRetries reports retry count', async () => {
    onbMocks.processCreatorOnboardingDigestRetries.mockResolvedValueOnce({ retried: 5, remaining: 2 });
    const o = mountOnb();
    await o.processWizardDigestRetries();
    expect(o.saveMessage.value).toContain('已重试 5');
    expect(o.saveMessage.value).toContain('剩余 2');
  });

  it('replayWizardDigestDeadLetter reports channel', async () => {
    onbMocks.replayCreatorOnboardingDigestDeadLetter.mockResolvedValueOnce({ channel: 'email' });
    const o = mountOnb();
    await o.replayWizardDigestDeadLetter();
    expect(o.saveMessage.value).toContain('email');
  });

  it('loadWizardWebhook populates state', async () => {
    onbMocks.fetchCreatorOnboardingWebhook.mockResolvedValueOnce({
      url: 'https://hook.example.com', enabled: true, signing_secret: 'secret123',
    });
    const o = mountOnb();
    await o.loadWizardWebhook();
    expect(o.wizardWebhookUrl.value).toBe('https://hook.example.com');
    expect(o.wizardWebhookEnabled.value).toBe(true);
    expect(o.wizardWebhookSigningSecret.value).toBe('secret123');
  });

  it('loadWizardWebhook handles failure', async () => {
    onbMocks.fetchCreatorOnboardingWebhook.mockRejectedValueOnce(new Error('down'));
    const o = mountOnb();
    await o.loadWizardWebhook();
    expect(o.wizardWebhookUrl.value).toBe('');
    expect(o.wizardWebhookEnabled.value).toBe(false);
  });

  it('saveWizardWebhook posts and saves message', async () => {
    onbMocks.saveCreatorOnboardingWebhook.mockResolvedValueOnce({});
    const o = mountOnb();
    o.wizardWebhookUrl.value = 'https://hook.example.com';
    await o.saveWizardWebhook();
    expect(o.saveMessage.value).toContain('Webhook');
  });

  it('loadWizardEmail populates state', async () => {
    onbMocks.fetchCreatorOnboardingEmail.mockResolvedValueOnce({
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
    onbMocks.saveCreatorOnboardingEmail.mockResolvedValueOnce({});
    const o = mountOnb();
    o.wizardEmailTo.value = 'a@b.com';
    await o.saveWizardEmail();
    expect(onbMocks.saveCreatorOnboardingEmail).toHaveBeenCalled();
    expect(o.saveMessage.value).toContain('邮件');
  });

  it('ackWizardNotifications reloads and shows count', async () => {
    onbMocks.ackCreatorOnboardingNotifications.mockResolvedValueOnce({ unread: 0, acked: 5 });
    const o = mountOnb();
    await o.ackWizardNotifications();
    expect(o.saveMessage.value).toContain('5');
    expect(o.saveMessage.value).toContain('已读');
  });

  it('ackWizardNotifications handles failure', async () => {
    onbMocks.ackCreatorOnboardingNotifications.mockRejectedValueOnce(new Error('fail'));
    const o = mountOnb();
    await o.ackWizardNotifications();
    expect(o.handleSaveError).toHaveBeenCalled();
  });
});