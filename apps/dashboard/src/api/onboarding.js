/**
 * Onboarding API
 *
 * Phase 62.7: 从 api/creator.js 拆出。
 *
 * 包含: Onboarding + Digest + Email + Webhook + Notifications + Share + Notes + DeadLetter (19 funcs)
 */

import { request } from './core.js';

export async function fetchCreatorOnboarding() {
  return request('/creator/onboarding');
}

export async function saveCreatorOnboardingProgress(body) {
  return request('/creator/onboarding/progress', {
    method: 'PUT',
    body,
  });
}

export async function applyCreatorOnboardingShare(body) {
  return request('/creator/onboarding/progress/apply-share', {
    method: 'POST',
    body,
  });
}

export async function saveCreatorOnboardingNotes(body) {
  return request('/creator/onboarding/notes', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorOnboardingNotifications(handle) {
  const params = handle ? `?handle=${encodeURIComponent(handle)}` : '';
  return request(`/creator/onboarding/notifications${params}`);
}

export async function ackCreatorOnboardingNotifications(body) {
  return request('/creator/onboarding/notifications/ack', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorOnboardingWebhook() {
  return request('/creator/onboarding/webhook');
}

export async function saveCreatorOnboardingWebhook(body) {
  return request('/creator/onboarding/webhook', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorOnboardingEmail() {
  return request('/creator/onboarding/email');
}

export async function saveCreatorOnboardingEmail(body) {
  return request('/creator/onboarding/email', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorOnboardingNotificationDigest(handle) {
  const params = handle ? `?handle=${encodeURIComponent(handle)}` : '';
  return request(`/creator/onboarding/notifications/digest${params}`);
}

export async function fetchCreatorOnboardingDigestSchedule() {
  return request('/creator/onboarding/notifications/digest/schedule');
}

export async function saveCreatorOnboardingDigestSchedule(body) {
  return request('/creator/onboarding/notifications/digest/schedule', {
    method: 'PUT',
    body,
  });
}

export async function dispatchCreatorOnboardingDigest(force = false) {
  const params = force ? '?force=true' : '';
  return request(`/creator/onboarding/notifications/digest/dispatch${params}`, {
    method: 'POST',
  });
}

export async function fetchCreatorOnboardingDigestRetryQueue() {
  return request('/creator/onboarding/notifications/digest/retry-queue');
}

export async function fetchCreatorOnboardingDigestStats() {
  return request('/creator/onboarding/notifications/digest/stats');
}

export async function processCreatorOnboardingDigestRetries() {
  return request('/creator/onboarding/notifications/digest/retry', {
    method: 'POST',
  });
}

export async function fetchCreatorOnboardingDigestDeadLetter() {
  return request('/creator/onboarding/notifications/digest/dead-letter');
}

export async function replayCreatorOnboardingDigestDeadLetter(body = {}) {
  return request('/creator/onboarding/notifications/digest/dead-letter/replay', {
    method: 'POST',
    body,
  });
}
