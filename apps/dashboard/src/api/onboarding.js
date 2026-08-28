/**
 * Phase 126 v16.2.3 shim: re-export from api/onboarding.ts typed wrapper,
 * plus legacy Creator-prefixed aliases used by existing composables.
 *
 * The original onboarding.js (legacy JS implementation, 19 functions) was
 * superseded by api/onboarding.ts (typed wrapper, 23 functions with new naming).
 *
 * This shim:
 * - Re-exports everything from ./onboarding.ts (new typed wrapper)
 * - Adds legacy `fetchCreatorOnboarding*` / `saveCreatorOnboarding*` aliases
 *   so existing composables (useCreatorOnboarding, useOnboardingNotifications,
 *   useWizardSteps) continue to work without modifications
 *
 * Will be deleted in v16.2.7 final cleanup once composables are refactored
 * to use the new typed wrapper names directly (T4 carryover to v16.2.4).
 */
import {
  fetchOnboardingWizard,
  saveOnboardingProgress,
  saveOnboardingNotes,
  applyWizardShareDone,
  collapseOnboardingWizard,
  dismissOnboardingWizard,
  fetchDiffCollabNotes,
  saveDiffCollabNotes,
  fetchOnboardingNotifications,
  ackOnboardingNotifications,
  buildOnboardingNotificationDigest,
  fetchDigestSchedule,
  saveDigestSchedule,
  fetchDigestDeadLetter,
  replayDigestDeadLetter,
  fetchDigestStats,
  fetchDigestRetryQueue,
  processDigestRetries,
  dispatchDigestNow,
  fetchOnboardingWebhookConfig,
  saveOnboardingWebhookConfig,
  fetchOnboardingEmailConfig,
  saveOnboardingEmailConfig,
} from './onboarding.ts';

// Re-export everything from the typed wrapper (canonical API)
export * from './onboarding.ts';

// Legacy Creator-prefixed aliases — preserved for backward compat with composables.
// Each alias simply re-exports the new typed wrapper function with the legacy name.

// Main wizard
export const fetchCreatorOnboarding = fetchOnboardingWizard;
export const saveCreatorOnboardingProgress = saveOnboardingProgress;
export const saveCreatorOnboardingNotes = saveOnboardingNotes;
export const applyCreatorOnboardingShare = applyWizardShareDone;
export const saveCreatorWizardPanelCollapsed = collapseOnboardingWizard;
export const dismissCreatorWizardPanel = dismissOnboardingWizard;

// Diff collab
export const fetchCreatorDiffCollabNotes = fetchDiffCollabNotes;
export const saveCreatorDiffCollabNotes = saveDiffCollabNotes;

// Notifications
export const fetchCreatorOnboardingNotifications = fetchOnboardingNotifications;
export const ackCreatorOnboardingNotifications = ackOnboardingNotifications;
export const fetchCreatorOnboardingNotificationDigest = buildOnboardingNotificationDigest;

// Digest schedule
export const fetchCreatorOnboardingDigestSchedule = fetchDigestSchedule;
export const saveCreatorOnboardingDigestSchedule = saveDigestSchedule;
export const fetchCreatorOnboardingDigestDeadLetter = fetchDigestDeadLetter;
export const replayCreatorOnboardingDigestDeadLetter = replayDigestDeadLetter;
export const fetchCreatorOnboardingDigestStats = fetchDigestStats;
export const fetchCreatorOnboardingDigestRetryQueue = fetchDigestRetryQueue;
export const processCreatorOnboardingDigestRetries = processDigestRetries;
export const dispatchCreatorOnboardingDigest = dispatchDigestNow;

// Webhook + Email
export const fetchCreatorOnboardingWebhook = fetchOnboardingWebhookConfig;
export const saveCreatorOnboardingWebhook = saveOnboardingWebhookConfig;
export const fetchCreatorOnboardingEmail = fetchOnboardingEmailConfig;
export const saveCreatorOnboardingEmail = saveOnboardingEmailConfig;
