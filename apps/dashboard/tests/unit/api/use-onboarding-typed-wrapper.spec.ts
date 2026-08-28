/**
 * Phase 126 v16.2.3 Task 6 (T3) URL contract regression test for onboarding.ts
 * typed wrapper.
 *
 * Goal: lock the URL contract to `/creator/onboarding*` (relative to
 * BASE_URL='/api') so the /api/api/ URL duplication bug cannot regress
 * (v16.2.1 lesson: world.ts/workspace.ts/quality.ts carry this bug to v16.2.7;
 * this wrapper is being authored AFTER the fix so it must NOT regress).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as onboardingApi from '@/api/onboarding';

describe('onboarding typed wrapper (v16.2.3 Task 6 / T3)', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({}),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // --- exports count: ≥20 wrappers per T3 spec ---

  it('exports ≥20 wrapper functions', () => {
    const wrappers = Object.entries(onboardingApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBeGreaterThanOrEqual(20);
  });

  // --- static: no /api/ prefix in any wrapper body (TYPE-level regression lock) ---

  it('no wrapper body hardcodes /api/ prefix', () => {
    const wrappers = Object.entries(onboardingApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/creator/);
      expect(src, `${name} should not contain 'fetch(' direct`).not.toMatch(/\bfetch\(/);
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('fetchOnboardingWizard GETs /api/creator/onboarding (no /api/api duplication)', async () => {
    await onboardingApi.fetchOnboardingWizard();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding');
  });

  it('saveOnboardingProgress PUTs /api/creator/onboarding/progress', async () => {
    await onboardingApi.saveOnboardingProgress({ completed_step_ids: [], step_notes: null });
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/onboarding/progress');
    expect(opts.method).toBe('PUT');
  });

  it('dismissOnboardingWizard PUTs /api/creator/onboarding/wizard-dismiss', async () => {
    await onboardingApi.dismissOnboardingWizard();
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/onboarding/wizard-dismiss');
    expect(opts.method).toBe('PUT');
  });

  it('collapseOnboardingWizard PUTs /api/creator/onboarding/wizard-collapse', async () => {
    await onboardingApi.collapseOnboardingWizard({ collapsed: true });
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/onboarding/wizard-collapse');
    expect(opts.method).toBe('PUT');
  });

  it('saveOnboardingNotes PUTs /api/creator/onboarding/notes', async () => {
    await onboardingApi.saveOnboardingNotes({ step_notes: {} });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/notes');
  });

  it('applyWizardShareDone POSTs /api/creator/onboarding/progress/apply-share', async () => {
    await onboardingApi.applyWizardShareDone();
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/onboarding/progress/apply-share');
    expect(opts.method).toBe('POST');
  });

  it('fetchDiffCollabNotes GETs /api/creator/diff-collab-notes (NOT under /onboarding/)', async () => {
    await onboardingApi.fetchDiffCollabNotes();
    const url = fetchMock.mock.calls[0][0];
    // v16.2.7 T2: backend mounts @app.get('/api/creator/diff-collab-notes') directly,
    // NOT under /api/creator/onboarding/. Earlier wrapper path was 404.
    expect(url).toBe('/api/creator/diff-collab-notes');
  });

  it('saveDiffCollabNotes PUTs /api/creator/diff-collab-notes (NOT under /onboarding/)', async () => {
    await onboardingApi.saveDiffCollabNotes({ notes: {} });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/diff-collab-notes');
  });

  it('fetchOnboardingNotifications GETs /api/creator/onboarding/notifications', async () => {
    await onboardingApi.fetchOnboardingNotifications();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/notifications');
  });

  it('ackOnboardingNotifications PUTs /api/creator/onboarding/notifications/ack', async () => {
    await onboardingApi.ackOnboardingNotifications({
      notification_ids: [],
      all_notifications: false,
      handle: null,
    });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/notifications/ack');
  });

  it('buildOnboardingNotificationDigest POSTs /api/creator/onboarding/notifications/digest', async () => {
    await onboardingApi.buildOnboardingNotificationDigest();
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/onboarding/notifications/digest');
    expect(opts.method).toBe('POST');
  });

  it('fetchDigestSchedule GETs /api/creator/onboarding/digest/schedule', async () => {
    await onboardingApi.fetchDigestSchedule();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/digest/schedule');
  });

  it('saveDigestSchedule PUTs /api/creator/onboarding/digest/schedule', async () => {
    await onboardingApi.saveDigestSchedule({
      enabled: true,
      interval_hours: 24,
    });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/digest/schedule');
  });

  it('fetchDigestDeadLetter GETs /api/creator/onboarding/digest/dead-letter', async () => {
    await onboardingApi.fetchDigestDeadLetter();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/digest/dead-letter');
  });

  it('replayDigestDeadLetter POSTs /api/creator/onboarding/digest/dead-letter/replay', async () => {
    await onboardingApi.replayDigestDeadLetter({ index: 0 });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/digest/dead-letter/replay');
  });

  it('fetchDigestStats GETs /api/creator/onboarding/digest/stats', async () => {
    await onboardingApi.fetchDigestStats();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/digest/stats');
  });

  it('fetchDigestRetryQueue GETs /api/creator/onboarding/digest/retry-queue', async () => {
    await onboardingApi.fetchDigestRetryQueue();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/digest/retry-queue');
  });

  it('processDigestRetries POSTs /api/creator/onboarding/digest/retry', async () => {
    await onboardingApi.processDigestRetries();
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/onboarding/digest/retry');
    expect(opts.method).toBe('POST');
  });

  it('dispatchDigestNow POSTs /api/creator/onboarding/digest/dispatch', async () => {
    await onboardingApi.dispatchDigestNow();
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/onboarding/digest/dispatch');
    expect(opts.method).toBe('POST');
  });

  it('fetchOnboardingWebhookConfig GETs /api/creator/onboarding/webhook', async () => {
    await onboardingApi.fetchOnboardingWebhookConfig();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/webhook');
  });

  it('saveOnboardingWebhookConfig PUTs /api/creator/onboarding/webhook', async () => {
    await onboardingApi.saveOnboardingWebhookConfig({ enabled: true, url: 'https://x' });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/webhook');
  });

  it('fetchOnboardingEmailConfig GETs /api/creator/onboarding/email', async () => {
    await onboardingApi.fetchOnboardingEmailConfig();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/email');
  });

  it('saveOnboardingEmailConfig PUTs /api/creator/onboarding/email', async () => {
    await onboardingApi.saveOnboardingEmailConfig({ enabled: true });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/onboarding/email');
  });
});
