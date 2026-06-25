/**
 * useCreatorOnboarding — 入门向导逻辑（从 CreatorPage 抽出）
 */
import { computed, nextTick, ref, watch } from 'vue';
import {
  fetchCreatorOnboarding,
  saveCreatorOnboardingProgress,
  applyCreatorOnboardingShare,
  saveCreatorOnboardingNotes,
  dismissCreatorWizardPanel,
  saveCreatorWizardPanelCollapsed,
  fetchCreatorOnboardingNotifications,
  fetchCreatorOnboardingNotificationDigest,
  fetchCreatorOnboardingDigestSchedule,
  saveCreatorOnboardingDigestSchedule,
  dispatchCreatorOnboardingDigest,
  fetchCreatorOnboardingDigestRetryQueue,
  fetchCreatorOnboardingDigestStats,
  processCreatorOnboardingDigestRetries,
  fetchCreatorOnboardingDigestDeadLetter,
  replayCreatorOnboardingDigestDeadLetter,
  ackCreatorOnboardingNotifications,
  fetchCreatorOnboardingWebhook,
  saveCreatorOnboardingWebhook,
  fetchCreatorOnboardingEmail,
  saveCreatorOnboardingEmail,
} from '../api/index.js';

const CREATION_MODE_ONBOARDING_STEPS = {
  companion: ['init', 'pillars', 'dashboard', 'write', 'check'],
  advance: ['init', 'pillars', 'dashboard', 'volume', 'batch', 'check'],
  studio: ['init', 'pillars', 'dashboard', 'volume', 'preflight', 'check'],
};

const CREATION_MODE_ONBOARDING_LABELS = {
  companion: '陪伴',
  advance: '推进',
  studio: '工作室',
};

const CREATION_MODE_ONBOARDING_FOCUS_STEP = {
  companion: 'write',
  advance: 'volume',
  studio: 'preflight',
};

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

const wizardPanelRef = ref(null);
const wizardPanelOpen = ref(false);
const wizardShareMessage = ref('');
const wizardStepNotes = ref({});
const wizardNotifications = ref([]);
const wizardUnreadMentions = ref(0);
const wizardNotificationHandleFilter = ref('');
const wizardNotificationHandles = ref([]);
const wizardWebhookUrl = ref('');
const wizardWebhookEnabled = ref(false);
const wizardEmailTo = ref('');
const wizardEmailSmtpHost = ref('');
const wizardEmailEnabled = ref(false);
const wizardNotificationDigest = ref({ unread: 0, group_count: 0, groups: [] });
const wizardDigestScheduleEnabled = ref(false);
const wizardDigestScheduleHours = ref(24);
const wizardDigestQuietStart = ref(null);
const wizardDigestQuietEnd = ref(null);
const wizardDigestHandleChannelsJson = ref('');
const wizardDigestHandleQuietJson = ref('');
const wizardDigestStats = ref({ sent_total: 0, failed_total: 0 });
const wizardDigestDeadLetter = ref({ item_count: 0, items: [] });
const wizardDigestRetryQueue = ref({ item_count: 0, items: [] });
const wizardWebhookSigningSecret = ref('');
const onboardingWizard = ref(null);
const completedWizardSteps = ref(new Set());
const autoCompletedWizardSteps = ref(new Set());

const focusWizardStepRef = focusWizardStep;

function extractMentionsFromText(text) {
  const re = /@([a-zA-Z][a-zA-Z0-9_-]{0,31})/g;
  const found = [];
  let match = re.exec(String(text || ''));
  while (match) {
    const handle = match[1].toLowerCase();
    if (!found.includes(handle)) found.push(handle);
    match = re.exec(String(text || ''));
  }
  return found;
}

function syncWizardPanelOpen() {
  if (focusWizard.value || focusWizardStepRef.value) {
    wizardPanelOpen.value = true;
    return;
  }
  if (wizardUnreadMentions.value > 0) {
    wizardPanelOpen.value = true;
    return;
  }
  const progress = onboardingWizard.value?.progress_pct ?? 100;
  if (progress >= 100 && !focusWizard.value) {
    wizardPanelOpen.value = false;
    return;
  }
  if (uiProfile.value.studio_wizard_collapse_memory && onboardingWizard.value) {
    wizardPanelOpen.value = !Boolean(onboardingWizard.value.wizard_panel_collapsed);
    return;
  }
  if (uiProfile.value.wizard_expand_if_incomplete) {
    const incomplete = (onboardingWizard.value?.progress_pct ?? 100) < 100;
    const dismissed = Boolean(onboardingWizard.value?.wizard_panel_dismissed);
    wizardPanelOpen.value = incomplete && !dismissed;
    return;
  }
  if (uiProfile.value.wizard_default_collapsed) {
    wizardPanelOpen.value = false;
    return;
  }
  wizardPanelOpen.value = Boolean(focusWizard.value);
}

async function loadOnboardingWizard() {
  try {
    onboardingWizard.value = await fetchCreatorOnboarding();
    completedWizardSteps.value = new Set(onboardingWizard.value?.completed_step_ids || []);
    autoCompletedWizardSteps.value = new Set(onboardingWizard.value?.auto_completed_step_ids || []);
    wizardStepNotes.value = { ...(onboardingWizard.value?.step_notes || {}) };
    wizardUnreadMentions.value = onboardingWizard.value?.unread_mention_count || 0;
    await loadWizardNotifications();
    if (wizardPanelOpen.value) {
      await nextTick();
      try {
        wizardPanelRef.value?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
      } catch {
        /* jsdom */
      }
    }
    await focusWizardStepFromUrl();
    await applyWizardShareFromUrl();
  } catch {
    onboardingWizard.value = null;
  }
}

function onWizardToggle(event) {
  wizardPanelOpen.value = event.target.open;
  if (uiProfile.value.studio_wizard_collapse_memory) {
    saveCreatorWizardPanelCollapsed(!event.target.open)
      .then((data) => {
        onboardingWizard.value = data;
      })
      .catch(() => {
        /* ignore collapse save errors */
      });
  } else if (!event.target.open && uiProfile.value.wizard_expand_if_incomplete) {
    dismissCreatorWizardPanel()
      .then((data) => {
        onboardingWizard.value = data;
      })
      .catch(() => {
        /* ignore dismiss errors */
      });
  }
  setWizardDeepLink(
    event.target.open,
    event.target.open ? focusWizardStepRef.value : null,
    event.target.open ? [...completedWizardSteps.value] : [],
    event.target.open ? { ...wizardStepNotes.value } : {},
  );
}

async function applyWizardShareFromUrl() {
  const done = focusWizardDone.value;
  const notes = focusWizardNotes.value;
  if (!done?.length && (!notes || !Object.keys(notes).length)) return;
  try {
    await applyCreatorOnboardingShare({
      completed_step_ids: done || [],
      step_notes: notes || {},
    });
    onboardingWizard.value = await fetchCreatorOnboarding();
    completedWizardSteps.value = new Set(onboardingWizard.value?.completed_step_ids || []);
    autoCompletedWizardSteps.value = new Set(onboardingWizard.value?.auto_completed_step_ids || []);
    wizardStepNotes.value = { ...(onboardingWizard.value?.step_notes || {}) };
  } catch {
    /* ignore share apply errors */
  }
}

async function saveWizardStepNote(stepId) {
  try {
    await saveCreatorOnboardingNotes({
      step_notes: { [stepId]: wizardStepNotes.value[stepId] || '' },
    });
    await loadWizardNotifications();
  } catch {
    /* ignore note save errors */
  }
}

async function copyWizardShareLink() {
  const url = buildWizardShareUrl(
    [...completedWizardSteps.value],
    focusWizardStepRef.value,
    wizardStepNotes.value,
  );
  try {
    await navigator.clipboard.writeText(url);
    wizardShareMessage.value = '已复制分享链接';
  } catch {
    wizardShareMessage.value = url;
  }
  setTimeout(() => {
    wizardShareMessage.value = '';
  }, 3000);
}

async function focusWizardStepFromUrl() {
  if (!focusWizardStepRef.value || !onboardingWizard.value) return;
  const exists = onboardingWizard.value.steps.some((s) => s.id === focusWizardStepRef.value);
  if (!exists) return;
  await nextTick();
  const el = document.querySelector(`[data-testid="wizard-step-${focusWizardStepRef.value}"]`);
  try {
    el?.closest('.wizard-step')?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
  } catch {
    /* jsdom */
  }
}

async function toggleWizardStep(stepId, checked) {
  const next = new Set(completedWizardSteps.value);
  if (checked) {
    next.add(stepId);
  } else {
    next.delete(stepId);
  }
  try {
    const result = await saveCreatorOnboardingProgress({
      completed_step_ids: [...next],
    });
    completedWizardSteps.value = new Set(result.completed_step_ids || []);
    autoCompletedWizardSteps.value = new Set(result.auto_completed_step_ids || []);
    if (onboardingWizard.value) {
      onboardingWizard.value = {
        ...onboardingWizard.value,
        completed_step_ids: result.completed_step_ids,
        auto_completed_step_ids: result.auto_completed_step_ids,
        progress_pct: result.progress_pct,
      };
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function loadWizardNotifications() {
  try {
    const handle = wizardNotificationHandleFilter.value || undefined;
    const data = await fetchCreatorOnboardingNotifications(handle);
    wizardNotifications.value = data.notifications || [];
    wizardNotificationHandles.value = data.handles || [];
    wizardUnreadMentions.value = data.unread ?? wizardNotifications.value.filter((n) => !n.read).length;
    const digest = await fetchCreatorOnboardingNotificationDigest(handle);
    wizardNotificationDigest.value = digest;
    await loadWizardDigestSchedule();
    await loadWizardWebhook();
    await loadWizardEmail();
  } catch {
    wizardNotifications.value = [];
    wizardNotificationHandles.value = [];
    wizardUnreadMentions.value = onboardingWizard.value?.unread_mention_count || 0;
    wizardNotificationDigest.value = { unread: 0, group_count: 0, groups: [] };
    wizardDigestScheduleEnabled.value = false;
    wizardDigestScheduleHours.value = 24;
  }
}

async function loadWizardDigestSchedule() {
  try {
    const data = await fetchCreatorOnboardingDigestSchedule();
    wizardDigestScheduleEnabled.value = Boolean(data.enabled);
    wizardDigestScheduleHours.value = data.interval_hours || 24;
    wizardDigestQuietStart.value = data.quiet_hours_start ?? null;
    wizardDigestQuietEnd.value = data.quiet_hours_end ?? null;
    wizardDigestHandleChannelsJson.value = JSON.stringify(data.handle_channels || {});
    wizardDigestHandleQuietJson.value = JSON.stringify(data.handle_quiet_hours || {});
    const stats = await fetchCreatorOnboardingDigestStats();
    wizardDigestStats.value = stats;
    const retry = await fetchCreatorOnboardingDigestRetryQueue();
    wizardDigestRetryQueue.value = retry;
    const deadLetter = await fetchCreatorOnboardingDigestDeadLetter();
    wizardDigestDeadLetter.value = deadLetter;
  } catch {
    wizardDigestScheduleEnabled.value = false;
    wizardDigestScheduleHours.value = 24;
    wizardDigestQuietStart.value = null;
    wizardDigestQuietEnd.value = null;
    wizardDigestRetryQueue.value = { item_count: 0, items: [] };
  }
}

async function saveWizardDigestSchedule() {
  try {
    let handleChannels = {};
    let handleQuietHours = {};
    if (wizardDigestHandleChannelsJson.value.trim()) {
      handleChannels = JSON.parse(wizardDigestHandleChannelsJson.value);
    }
    if (wizardDigestHandleQuietJson.value.trim()) {
      handleQuietHours = JSON.parse(wizardDigestHandleQuietJson.value);
    }
    await saveCreatorOnboardingDigestSchedule({
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

async function processWizardDigestRetries() {
  try {
    const result = await processCreatorOnboardingDigestRetries();
    saveMessage.value = `已重试 ${result.retried} 条，剩余 ${result.remaining}`;
    await loadWizardDigestSchedule();
  } catch (e) {
    handleSaveError(e);
  }
}

async function replayWizardDigestDeadLetter() {
  try {
    const result = await replayCreatorOnboardingDigestDeadLetter({ index: 0 });
    saveMessage.value = `已重放死信（${result.channel || 'unknown'}）`;
    await loadWizardDigestSchedule();
  } catch (e) {
    handleSaveError(e);
  }
}

async function dispatchWizardDigest() {
  try {
    const result = await dispatchCreatorOnboardingDigest(true);
    saveMessage.value = result.sent ? '已发送 digest' : `跳过：${result.reason || '未知'}`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function loadWizardWebhook() {
  try {
    const data = await fetchCreatorOnboardingWebhook();
    wizardWebhookUrl.value = data.url || '';
    wizardWebhookEnabled.value = Boolean(data.enabled);
    wizardWebhookSigningSecret.value = data.signing_secret || '';
  } catch {
    wizardWebhookUrl.value = '';
    wizardWebhookEnabled.value = false;
  }
}

async function saveWizardWebhook() {
  try {
    await saveCreatorOnboardingWebhook({
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

async function loadWizardEmail() {
  try {
    const data = await fetchCreatorOnboardingEmail();
    wizardEmailTo.value = (data.to_addresses || []).join(', ');
    wizardEmailSmtpHost.value = data.smtp_host || '';
    wizardEmailEnabled.value = Boolean(data.enabled);
  } catch {
    wizardEmailTo.value = '';
    wizardEmailSmtpHost.value = '';
    wizardEmailEnabled.value = false;
  }
}

async function saveWizardEmail() {
  try {
    const toAddresses = wizardEmailTo.value
      .split(',')
      .map((addr) => addr.trim())
      .filter(Boolean);
    await saveCreatorOnboardingEmail({
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

async function ackWizardNotifications() {
  try {
    const result = await ackCreatorOnboardingNotifications({
      all_notifications: true,
      handle: wizardNotificationHandleFilter.value || undefined,
    });
    wizardUnreadMentions.value = result.unread ?? 0;
    await loadWizardNotifications();
    saveMessage.value = `已标记 ${result.acked} 条通知为已读`;
  } catch (e) {
    handleSaveError(e);
  }
}

function wizardMentionsForStep(stepId) {
  const fromApi = onboardingWizard.value?.step_mentions?.[stepId];
  if (fromApi?.length) return fromApi;
  return extractMentionsFromText(wizardStepNotes.value[stepId] || '');
}

function onboardingModesForStep(stepId) {
  if (!uiProfile.value.creation_mode_onboarding_step_link) return [];
  return Object.entries(CREATION_MODE_ONBOARDING_STEPS)
    .filter(([, steps]) => steps.includes(stepId))
    .map(([mode]) => ({ mode, label: CREATION_MODE_ONBOARDING_LABELS[mode] }));
}

function isOnboardingStepLinkedToCurrentMode(stepId) {
  if (!uiProfile.value.creation_mode_onboarding_step_link || !overview.value) return false;
  const steps = CREATION_MODE_ONBOARDING_STEPS[overview.value.creation_mode] || [];
  return steps.includes(stepId);
}

async function linkModeToOnboardingStep(mode) {
  if (!uiProfile.value.creation_mode_onboarding_step_link || !mode) return;
  const firstStep = CREATION_MODE_ONBOARDING_FOCUS_STEP[mode];
  if (!firstStep) return;
  wizardPanelOpen.value = true;
  setWizardDeepLink(true, firstStep);
  await nextTick();
  await focusWizardStepFromUrl();
  saveMessage.value = `已联动 ${CREATION_MODE_ONBOARDING_LABELS[mode] || mode} 向导步骤`;
}

watch(onboardingWizard, () => {
  if (uiProfile.value.studio_wizard_collapse_memory) {
    syncWizardPanelOpen();
  }
});

const panelContext = {
  uiProfile,
  wizardPanelRef,
  wizardPanelOpen,
  onboardingWizard,
  wizardUnreadMentions,
  wizardNotifications,
  wizardNotificationHandles,
  wizardNotificationHandleFilter,
  wizardNotificationDigest,
  wizardDigestScheduleEnabled,
  wizardDigestScheduleHours,
  wizardDigestStats,
  wizardDigestHandleChannelsJson,
  wizardDigestHandleQuietJson,
  wizardDigestQuietStart,
  wizardDigestQuietEnd,
  wizardDigestRetryQueue,
  wizardDigestDeadLetter,
  wizardWebhookEnabled,
  wizardWebhookUrl,
  wizardWebhookSigningSecret,
  wizardEmailEnabled,
  wizardEmailTo,
  wizardEmailSmtpHost,
  completedWizardSteps,
  focusWizardStep: focusWizardStepRef,
  autoCompletedWizardSteps,
  wizardStepNotes,
  wizardShareMessage,
  onWizardToggle,
  loadWizardNotifications,
  saveWizardDigestSchedule,
  dispatchWizardDigest,
  processWizardDigestRetries,
  replayWizardDigestDeadLetter,
  ackWizardNotifications,
  saveWizardWebhook,
  saveWizardEmail,
  toggleWizardStep,
  saveWizardStepNote,
  wizardMentionsForStep,
  onboardingModesForStep,
  isOnboardingStepLinkedToCurrentMode,
  copyWizardShareLink,
};

return {
  panelContext,
  wizardEmailTo,
  onboardingWizard,
  loadOnboardingWizard,
  syncWizardPanelOpen,
  linkModeToOnboardingStep,
};
}
