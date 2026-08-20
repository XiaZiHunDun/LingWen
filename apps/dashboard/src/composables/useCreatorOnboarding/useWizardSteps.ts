/**
 * useWizardSteps — 向导步骤 + 分享/链接 + note/复选
 *
 * Phase 19 Task 7：从 useCreatorOnboarding.js 拆出（完整实现）。
 * 负责: wizard state + loadOnboardingWizard + toggleWizardStep +
 *       saveWizardStepNote + onWizardToggle + syncWizardPanelOpen +
 *       copyWizardShareLink + applyWizardShareFromUrl + focusWizardStepFromUrl +
 *       extractMentionsFromText + showOnboardingChrome computed。
 *
 * 注: wizardUnreadMentions 是与 useOnboardingNotifications 共享状态，通过 deps 传入。
 *     setWizardDeepLink 是外部 navigator 函数，通过 deps 传入。
 */
import { computed, nextTick, ref, watch } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchCreatorOnboarding,
  saveCreatorOnboardingProgress,
  saveCreatorOnboardingNotes,
  applyCreatorOnboardingShare,
  saveCreatorWizardPanelCollapsed,
  dismissCreatorWizardPanel,
} from '../../api/index.js';
import { isCreatorChromeVisible, isHumanFirstDeskMode } from '../../config/creatorPanelMatrix.js';
import { logger } from '../../utils/logger.js';

interface WizardStep {
  id: string;
  title?: string;
  description?: string;
  done?: boolean;
}

interface OnboardingWizard {
  steps: WizardStep[];
  completed_step_ids?: string[];
  auto_completed_step_ids?: string[];
  step_notes?: Record<string, string>;
  step_mentions?: Record<string, string[]>;
  unread_mention_count?: number;
  progress_pct?: number;
  wizard_panel_collapsed?: boolean;
  wizard_panel_dismissed?: boolean;
}

export interface WizardStepsDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  overview: Ref<Record<string, unknown> | null>;
  error: Ref<string | null>;
  focusWizard: Ref<boolean>;
  focusWizardStep: Ref<string | null>;
  focusWizardDone: Ref<string[]>;
  focusWizardNotes: Ref<Record<string, string>>;
  wizardUnreadMentions: Ref<number>;
  loadWizardNotifications: () => Promise<void>;
  setWizardDeepLink: (open: boolean, step?: string | null, done?: string[], notes?: Record<string, string>) => void;
  buildWizardShareUrl: (done: string[], step: string | null, notes: Record<string, string>) => string;
}

export interface WizardStepsReturn {
  wizardPanelRef: Ref<HTMLElement | null>;
  wizardPanelOpen: Ref<boolean>;
  wizardShareMessage: Ref<string>;
  wizardStepNotes: Ref<Record<string, string>>;
  onboardingWizard: Ref<OnboardingWizard | null>;
  completedWizardSteps: Ref<Set<string>>;
  autoCompletedWizardSteps: Ref<Set<string>>;
  showOnboardingChrome: ComputedRef<boolean>;
  loadOnboardingWizard: () => Promise<void>;
  onWizardToggle: (event: { target: { open: boolean } }) => void;
  syncWizardPanelOpen: () => void;
  applyWizardShareFromUrl: () => Promise<void>;
  saveWizardStepNote: (stepId: string) => Promise<void>;
  copyWizardShareLink: () => Promise<void>;
  focusWizardStepFromUrl: () => Promise<void>;
  toggleWizardStep: (stepId: string, checked: boolean) => Promise<void>;
  extractMentionsFromText: (text: string) => string[];
}

export function useWizardSteps(deps: WizardStepsDeps): WizardStepsReturn {
  const {
    uiProfile,
    overview,
    error,
    focusWizard,
    focusWizardStep,
    focusWizardDone,
    focusWizardNotes,
    wizardUnreadMentions,
    loadWizardNotifications,
    setWizardDeepLink,
    buildWizardShareUrl,
  } = deps;

  const wizardPanelRef = ref<HTMLElement | null>(null);
  const wizardPanelOpen = ref(false);
  const wizardShareMessage = ref('');
  const wizardStepNotes = ref<Record<string, string>>({});
  const onboardingWizard = ref<OnboardingWizard | null>(null);
  const completedWizardSteps = ref(new Set<string>());
  const autoCompletedWizardSteps = ref(new Set<string>());

  function extractMentionsFromText(text: string): string[] {
    const re = /@([a-zA-Z][a-zA-Z0-9_-]{0,31})/g;
    const found: string[] = [];
    const src = String(text || '');
    let match = re.exec(src);
    while (match) {
      const handle = match[1].toLowerCase();
      if (!found.includes(handle)) found.push(handle);
      match = re.exec(src);
    }
    return found;
  }

  function syncWizardPanelOpen(): void {
    if (focusWizard.value || focusWizardStep.value) {
      wizardPanelOpen.value = true;
      return;
    }
    if (wizardUnreadMentions.value > 0) {
      wizardPanelOpen.value = true;
      return;
    }
    // 伴侣书桌：默认收起向导，避免挡住写作区（URL ?wizard= 或 @提及 仍展开）
    if (isHumanFirstDeskMode((overview.value as { creation_mode?: string } | null)?.creation_mode)) {
      wizardPanelOpen.value = false;
      return;
    }
    const progress = onboardingWizard.value?.progress_pct ?? 100;
    if (progress >= 100 && !focusWizard.value) {
      wizardPanelOpen.value = false;
      return;
    }
    if ((uiProfile.value as { studio_wizard_collapse_memory?: boolean }).studio_wizard_collapse_memory && onboardingWizard.value) {
      wizardPanelOpen.value = !Boolean(onboardingWizard.value.wizard_panel_collapsed);
      return;
    }
    if ((uiProfile.value as { wizard_expand_if_incomplete?: boolean }).wizard_expand_if_incomplete) {
      const incomplete = (onboardingWizard.value?.progress_pct ?? 100) < 100;
      const dismissed = Boolean(onboardingWizard.value?.wizard_panel_dismissed);
      wizardPanelOpen.value = incomplete && !dismissed;
      return;
    }
    if ((uiProfile.value as { wizard_default_collapsed?: boolean }).wizard_default_collapsed) {
      wizardPanelOpen.value = false;
      return;
    }
    wizardPanelOpen.value = Boolean(focusWizard.value);
  }

  async function loadOnboardingWizard(): Promise<void> {
    try {
      const data = await fetchCreatorOnboarding() as OnboardingWizard;
      onboardingWizard.value = data;
      completedWizardSteps.value = new Set(data?.completed_step_ids || []);
      autoCompletedWizardSteps.value = new Set(data?.auto_completed_step_ids || []);
      wizardStepNotes.value = { ...(data?.step_notes || {}) };
      wizardUnreadMentions.value = data?.unread_mention_count || 0;
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

  function onWizardToggle(event: { target: { open: boolean } }): void {
    wizardPanelOpen.value = event.target.open;
    if ((uiProfile.value as { studio_wizard_collapse_memory?: boolean }).studio_wizard_collapse_memory) {
      saveCreatorWizardPanelCollapsed(!event.target.open)
        .then((data) => {
          onboardingWizard.value = data as OnboardingWizard;
        })
        .catch((err) => {
          logger.warn('saveCreatorWizardPanelCollapsed failed', err);
        });
    } else if (!event.target.open && (uiProfile.value as { wizard_expand_if_incomplete?: boolean }).wizard_expand_if_incomplete) {
      dismissCreatorWizardPanel()
        .then((data) => {
          onboardingWizard.value = data as OnboardingWizard;
        })
        .catch((err) => {
          logger.warn('dismissCreatorWizardPanel failed', err);
        });
    }
    setWizardDeepLink(
      event.target.open,
      event.target.open ? focusWizardStep.value : null,
      event.target.open ? [...completedWizardSteps.value] : [],
      event.target.open ? { ...wizardStepNotes.value } : {},
    );
  }

  async function applyWizardShareFromUrl(): Promise<void> {
    const done = focusWizardDone.value;
    const notes = focusWizardNotes.value;
    if (!done?.length && (!notes || !Object.keys(notes).length)) return;
    try {
      await applyCreatorOnboardingShare({
        completed_step_ids: done || [],
        step_notes: notes || {},
      });
      const fresh = await fetchCreatorOnboarding() as OnboardingWizard;
      onboardingWizard.value = fresh;
      completedWizardSteps.value = new Set(fresh?.completed_step_ids || []);
      autoCompletedWizardSteps.value = new Set(fresh?.auto_completed_step_ids || []);
      wizardStepNotes.value = { ...(fresh?.step_notes || {}) };
    } catch {
      /* ignore share apply errors */
    }
  }

  async function saveWizardStepNote(stepId: string): Promise<void> {
    try {
      await saveCreatorOnboardingNotes({
        step_notes: { [stepId]: wizardStepNotes.value[stepId] || '' },
      });
      await loadWizardNotifications();
    } catch {
      /* ignore note save errors */
    }
  }

  async function copyWizardShareLink(): Promise<void> {
    const url = buildWizardShareUrl(
      [...completedWizardSteps.value],
      focusWizardStep.value,
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

  async function focusWizardStepFromUrl(): Promise<void> {
    if (!focusWizardStep.value || !onboardingWizard.value) return;
    const exists = onboardingWizard.value.steps.some((s) => s.id === focusWizardStep.value);
    if (!exists) return;
    await nextTick();
    const el = document.querySelector(`[data-testid="wizard-step-${focusWizardStep.value}"]`);
    try {
      (el as HTMLElement | null)?.closest('.wizard-step')?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
    } catch {
      /* jsdom */
    }
  }

  async function toggleWizardStep(stepId: string, checked: boolean): Promise<void> {
    const next = new Set(completedWizardSteps.value);
    if (checked) {
      next.add(stepId);
    } else {
      next.delete(stepId);
    }
    try {
      const result = await saveCreatorOnboardingProgress({
        completed_step_ids: [...next],
      }) as { completed_step_ids?: string[]; auto_completed_step_ids?: string[]; progress_pct?: number };
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

  const showOnboardingChrome = computed<boolean>(() =>
    isCreatorChromeVisible(
      (overview.value as { creation_mode?: string } | null)?.creation_mode,
      'onboardingWizard',
    ),
  );

  watch(onboardingWizard, () => {
    if ((uiProfile.value as { studio_wizard_collapse_memory?: boolean }).studio_wizard_collapse_memory) {
      syncWizardPanelOpen();
    }
  });

  return {
    wizardPanelRef,
    wizardPanelOpen,
    wizardShareMessage,
    wizardStepNotes,
    onboardingWizard,
    completedWizardSteps,
    autoCompletedWizardSteps,
    showOnboardingChrome,
    loadOnboardingWizard,
    onWizardToggle,
    syncWizardPanelOpen,
    applyWizardShareFromUrl,
    saveWizardStepNote,
    copyWizardShareLink,
    focusWizardStepFromUrl,
    toggleWizardStep,
    extractMentionsFromText,
  };
}
