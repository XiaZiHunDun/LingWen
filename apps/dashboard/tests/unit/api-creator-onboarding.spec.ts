/**
 * api/onboarding 独立测试（Phase 62.7）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorOnboarding,
  saveCreatorOnboardingProgress,
  applyCreatorOnboardingShare,
  saveCreatorOnboardingNotes,
  fetchCreatorOnboardingNotifications,
  ackCreatorOnboardingNotifications,
  fetchCreatorOnboardingWebhook,
  saveCreatorOnboardingWebhook,
  fetchCreatorOnboardingEmail,
  saveCreatorOnboardingEmail,
  fetchCreatorOnboardingNotificationDigest,
  fetchCreatorOnboardingDigestSchedule,
  saveCreatorOnboardingDigestSchedule,
  dispatchCreatorOnboardingDigest,
  fetchCreatorOnboardingDigestRetryQueue,
  fetchCreatorOnboardingDigestStats,
  processCreatorOnboardingDigestRetries,
  fetchCreatorOnboardingDigestDeadLetter,
  replayCreatorOnboardingDigestDeadLetter,
} from '../../src/api/onboarding.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/onboarding', () => {
  it('fetchCreatorOnboarding GETs /creator/onboarding', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await fetchCreatorOnboarding();
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding');
  });

  it('saveCreatorOnboardingProgress PUTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorOnboardingProgress({ step: 1 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/progress', {
      method: 'PUT',
      body: { step: 1 },
    });
  });

  it('applyCreatorOnboardingShare POSTs body to progress/apply-share', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await applyCreatorOnboardingShare({ shareId: 's1' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/progress/apply-share', {
      method: 'POST',
      body: { shareId: 's1' },
    });
  });

  it('saveCreatorOnboardingNotes PUTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorOnboardingNotes({ notes: 'foo' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/notes', {
      method: 'PUT',
      body: { notes: 'foo' },
    });
  });

  it('fetchCreatorOnboardingNotifications GETs with encoded handle query string', async () => {
    mocks.request.mockResolvedValueOnce({ notifications: [] });
    await fetchCreatorOnboardingNotifications('handle/1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications?handle=handle%2F1',
    );
  });

  it('fetchCreatorOnboardingNotifications GETs without query when handle is empty', async () => {
    mocks.request.mockResolvedValueOnce({ notifications: [] });
    await fetchCreatorOnboardingNotifications('');
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/notifications');
  });

  it('ackCreatorOnboardingNotifications POSTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await ackCreatorOnboardingNotifications({ ids: ['n1'] });
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/notifications/ack', {
      method: 'POST',
      body: { ids: ['n1'] },
    });
  });

  it('fetchCreatorOnboardingWebhook GETs', async () => {
    mocks.request.mockResolvedValueOnce({ webhook: {} });
    await fetchCreatorOnboardingWebhook();
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/webhook');
  });

  it('saveCreatorOnboardingWebhook PUTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorOnboardingWebhook({ url: 'https://x' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/webhook', {
      method: 'PUT',
      body: { url: 'https://x' },
    });
  });

  it('fetchCreatorOnboardingEmail GETs', async () => {
    mocks.request.mockResolvedValueOnce({ email: {} });
    await fetchCreatorOnboardingEmail();
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/email');
  });

  it('saveCreatorOnboardingEmail PUTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorOnboardingEmail({ subject: 'foo' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/email', {
      method: 'PUT',
      body: { subject: 'foo' },
    });
  });

  it('fetchCreatorOnboardingNotificationDigest GETs with encoded handle query string', async () => {
    mocks.request.mockResolvedValueOnce({ digest: {} });
    await fetchCreatorOnboardingNotificationDigest('h/1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest?handle=h%2F1',
    );
  });

  it('fetchCreatorOnboardingNotificationDigest GETs without query when handle is empty', async () => {
    mocks.request.mockResolvedValueOnce({ digest: {} });
    await fetchCreatorOnboardingNotificationDigest('');
    expect(mocks.request).toHaveBeenCalledWith('/creator/onboarding/notifications/digest');
  });

  it('fetchCreatorOnboardingDigestSchedule GETs schedule', async () => {
    mocks.request.mockResolvedValueOnce({ schedule: {} });
    await fetchCreatorOnboardingDigestSchedule();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/schedule',
    );
  });

  it('saveCreatorOnboardingDigestSchedule PUTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorOnboardingDigestSchedule({ cron: '0 0 *' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/schedule',
      { method: 'PUT', body: { cron: '0 0 *' } },
    );
  });

  it('dispatchCreatorOnboardingDigest POSTs without force', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await dispatchCreatorOnboardingDigest();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/dispatch',
      { method: 'POST' },
    );
  });

  it('dispatchCreatorOnboardingDigest POSTs with force=true', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await dispatchCreatorOnboardingDigest(true);
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/dispatch?force=true',
      { method: 'POST' },
    );
  });

  it('fetchCreatorOnboardingDigestRetryQueue GETs', async () => {
    mocks.request.mockResolvedValueOnce({ queue: [] });
    await fetchCreatorOnboardingDigestRetryQueue();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/retry-queue',
    );
  });

  it('fetchCreatorOnboardingDigestStats GETs', async () => {
    mocks.request.mockResolvedValueOnce({ stats: {} });
    await fetchCreatorOnboardingDigestStats();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/stats',
    );
  });

  it('processCreatorOnboardingDigestRetries POSTs to retry', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await processCreatorOnboardingDigestRetries();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/retry',
      { method: 'POST' },
    );
  });

  it('fetchCreatorOnboardingDigestDeadLetter GETs', async () => {
    mocks.request.mockResolvedValueOnce({ deadLetter: [] });
    await fetchCreatorOnboardingDigestDeadLetter();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/dead-letter',
    );
  });

  it('replayCreatorOnboardingDigestDeadLetter POSTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await replayCreatorOnboardingDigestDeadLetter({ ids: ['d1'] });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/dead-letter/replay',
      { method: 'POST', body: { ids: ['d1'] } },
    );
  });

  it('replayCreatorOnboardingDigestDeadLetter defaults body to empty object', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await replayCreatorOnboardingDigestDeadLetter();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/onboarding/notifications/digest/dead-letter/replay',
      { method: 'POST', body: {} },
    );
  });
});