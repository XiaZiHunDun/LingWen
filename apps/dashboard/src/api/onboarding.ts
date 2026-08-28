/**
 * Onboarding API client — typed wrapper around /creator/onboarding* endpoints.
 *
 * Types come from @lingwen/dashboard-contracts/shared/creator (which mirrors
 * packages/lingwen-shared Pydantic DTOs via codegen).
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.3 (Phase 126 T3).
 * Existing api/onboarding.js / api/onboardingXxx.js continue to handle
 * backward-compatible calls. Future v16.2+ phases will switch them over.
 */
import type {
  CreatorDiffCollabNotesRequest,
  CreatorDiffCollabNotesResponse,
  CreatorOnboardingDigestDeadLetterReplayRequest,
  CreatorOnboardingDigestDeadLetterReplayResponse,
  CreatorOnboardingDigestDeadLetterResponse,
  CreatorOnboardingDigestDispatchResponse,
  CreatorOnboardingDigestDispatchStats,
  CreatorOnboardingDigestRetryProcessResponse,
  CreatorOnboardingDigestRetryQueueResponse,
  CreatorOnboardingDigestScheduleConfig,
  CreatorOnboardingDigestScheduleSaveRequest,
  CreatorOnboardingEmailConfig,
  CreatorOnboardingEmailSaveRequest,
  CreatorOnboardingNotesRequest,
  CreatorOnboardingNotificationDigestResponse,
  CreatorOnboardingNotificationsAckRequest,
  CreatorOnboardingNotificationsAckResponse,
  CreatorOnboardingNotificationsResponse,
  CreatorOnboardingProgressRequest,
  CreatorOnboardingProgressResponse,
  CreatorOnboardingResponse,
  CreatorOnboardingWebhookConfig,
  CreatorOnboardingWebhookSaveRequest,
  CreatorWizardPanelCollapsedRequest,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /creator/onboarding (main wizard)
// ---------------------------------------------------------------------------

export async function fetchOnboardingWizard(): Promise<CreatorOnboardingResponse> {
  const data = await request('/creator/onboarding');
  return data as CreatorOnboardingResponse;
}

export async function saveOnboardingProgress(
  req: CreatorOnboardingProgressRequest,
): Promise<CreatorOnboardingProgressResponse> {
  const data = await request('/creator/onboarding/progress', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorOnboardingProgressResponse;
}

export async function dismissOnboardingWizard(): Promise<CreatorOnboardingResponse> {
  const data = await request('/creator/onboarding/wizard-dismiss', {
    method: 'PUT',
  });
  return data as CreatorOnboardingResponse;
}

export async function collapseOnboardingWizard(
  req: CreatorWizardPanelCollapsedRequest,
): Promise<CreatorOnboardingResponse> {
  const data = await request('/creator/onboarding/wizard-collapse', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorOnboardingResponse;
}

export async function saveOnboardingNotes(
  req: CreatorOnboardingNotesRequest,
): Promise<CreatorOnboardingProgressResponse> {
  const data = await request('/creator/onboarding/notes', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorOnboardingProgressResponse;
}

export async function applyWizardShareDone(
  req?: CreatorOnboardingProgressRequest,
): Promise<CreatorOnboardingProgressResponse> {
  const data = await request('/creator/onboarding/progress/apply-share', {
    method: 'POST',
    ...(req ? { body: req } : {}),
  });
  return data as CreatorOnboardingProgressResponse;
}

// ---------------------------------------------------------------------------
// /creator/diff-collab-notes  (mounted on app, NOT under /creator/onboarding/)
// ---------------------------------------------------------------------------

export async function fetchDiffCollabNotes(): Promise<CreatorDiffCollabNotesResponse> {
  const data = await request('/creator/diff-collab-notes');
  return data as CreatorDiffCollabNotesResponse;
}

export async function saveDiffCollabNotes(
  req: CreatorDiffCollabNotesRequest,
): Promise<CreatorDiffCollabNotesResponse> {
  const data = await request('/creator/diff-collab-notes', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorDiffCollabNotesResponse;
}

// ---------------------------------------------------------------------------
// /creator/onboarding/notifications (list + ack + digest)
// ---------------------------------------------------------------------------

export async function fetchOnboardingNotifications(): Promise<CreatorOnboardingNotificationsResponse> {
  const data = await request('/creator/onboarding/notifications');
  return data as CreatorOnboardingNotificationsResponse;
}

export async function ackOnboardingNotifications(
  req: CreatorOnboardingNotificationsAckRequest,
): Promise<CreatorOnboardingNotificationsAckResponse> {
  const data = await request('/creator/onboarding/notifications/ack', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorOnboardingNotificationsAckResponse;
}

export async function buildOnboardingNotificationDigest(): Promise<CreatorOnboardingNotificationDigestResponse> {
  const data = await request('/creator/onboarding/notifications/digest', {
    method: 'POST',
  });
  return data as CreatorOnboardingNotificationDigestResponse;
}

// ---------------------------------------------------------------------------
// /creator/onboarding/digest/* (schedule + retry + dead-letter + dispatch)
// ---------------------------------------------------------------------------

export async function fetchDigestSchedule(): Promise<CreatorOnboardingDigestScheduleConfig> {
  const data = await request('/creator/onboarding/digest/schedule');
  return data as CreatorOnboardingDigestScheduleConfig;
}

export async function saveDigestSchedule(
  req: CreatorOnboardingDigestScheduleSaveRequest,
): Promise<CreatorOnboardingDigestScheduleConfig> {
  const data = await request('/creator/onboarding/digest/schedule', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorOnboardingDigestScheduleConfig;
}

export async function fetchDigestDeadLetter(): Promise<CreatorOnboardingDigestDeadLetterResponse> {
  const data = await request('/creator/onboarding/digest/dead-letter');
  return data as CreatorOnboardingDigestDeadLetterResponse;
}

export async function replayDigestDeadLetter(
  req: CreatorOnboardingDigestDeadLetterReplayRequest,
): Promise<CreatorOnboardingDigestDeadLetterReplayResponse> {
  const data = await request('/creator/onboarding/digest/dead-letter/replay', {
    method: 'POST',
    body: req,
  });
  return data as CreatorOnboardingDigestDeadLetterReplayResponse;
}

export async function fetchDigestStats(): Promise<CreatorOnboardingDigestDispatchStats> {
  const data = await request('/creator/onboarding/digest/stats');
  return data as CreatorOnboardingDigestDispatchStats;
}

export async function fetchDigestRetryQueue(): Promise<CreatorOnboardingDigestRetryQueueResponse> {
  const data = await request('/creator/onboarding/digest/retry-queue');
  return data as CreatorOnboardingDigestRetryQueueResponse;
}

export async function processDigestRetries(): Promise<CreatorOnboardingDigestRetryProcessResponse> {
  const data = await request('/creator/onboarding/digest/retry', {
    method: 'POST',
  });
  return data as CreatorOnboardingDigestRetryProcessResponse;
}

export async function dispatchDigestNow(
  force: boolean = false,
): Promise<CreatorOnboardingDigestDispatchResponse> {
  const path = force
    ? '/creator/onboarding/digest/dispatch?force=true'
    : '/creator/onboarding/digest/dispatch';
  const data = await request(path, {
    method: 'POST',
  });
  return data as CreatorOnboardingDigestDispatchResponse;
}

// ---------------------------------------------------------------------------
// /creator/onboarding/webhook + /email
// ---------------------------------------------------------------------------

export async function fetchOnboardingWebhookConfig(): Promise<CreatorOnboardingWebhookConfig> {
  const data = await request('/creator/onboarding/webhook');
  return data as CreatorOnboardingWebhookConfig;
}

export async function saveOnboardingWebhookConfig(
  req: CreatorOnboardingWebhookSaveRequest,
): Promise<CreatorOnboardingWebhookConfig> {
  const data = await request('/creator/onboarding/webhook', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorOnboardingWebhookConfig;
}

export async function fetchOnboardingEmailConfig(): Promise<CreatorOnboardingEmailConfig> {
  const data = await request('/creator/onboarding/email');
  return data as CreatorOnboardingEmailConfig;
}

export async function saveOnboardingEmailConfig(
  req: CreatorOnboardingEmailSaveRequest,
): Promise<CreatorOnboardingEmailConfig> {
  const data = await request('/creator/onboarding/email', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorOnboardingEmailConfig;
}
