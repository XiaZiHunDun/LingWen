/**
 * useCreatorModeGuide — 三模式说明与切换逻辑（从 CreatorPage 抽出）
 */
import { computed, ref } from 'vue';
import { CREATION_MODE_CAPABILITY_ROWS, isCreatorChromeVisible } from '../config/creatorPanelMatrix.js';

const CREATION_MODE_ONBOARDING_LABELS = {
  companion: '陪伴',
  advance: '推进',
  studio: '工作室',
};

const CREATION_MODE_HOTKEY_MODES = {
  1: 'companion',
  2: 'advance',
  3: 'studio',
};

const CREATION_MODE_SWITCH_HISTORY_KEY = 'creator_mode_switch_history';

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   onboardingWizard: import('vue').Ref<object|null>,
 *   linkModeToOnboardingStep: (mode: string) => Promise<void>,
 *   modeLabel: import('vue').ComputedRef<string>,
 * } deps
 */
export function useCreatorModeGuide(deps) {
  const { uiProfile, overview, saveMessage, onboardingWizard, linkModeToOnboardingStep, modeLabel } = deps;

const pendingModeSwitch = ref(null);
const creationModeSwitchHistory = ref([]);
const lastModeSwitchUndo = ref(null);
const creationModeSwitchAriaMessage = ref('');

const creationModeSwitchHintText = computed(() => {
  if (!uiProfile.value.creation_mode_switch_hint || !overview.value) return '';
  const mode = overview.value.creation_mode;
  if (mode === 'companion') {
    return '陪伴模式：人主笔 + P0 守门。切换推进请编辑 config/project.yaml → creation_mode: advance';
  }
  if (mode === 'advance') {
    return '推进模式：人定卷纲 + batch 产章。切换陪伴请编辑 config/project.yaml → creation_mode: companion';
  }
  return '';
});

const creationModePreviewRows = computed(() => {
  if (!uiProfile.value.creation_mode_switch_preview || !overview.value) return [];
  const current = overview.value.creation_mode;
  return [
    { mode: 'companion', label: '陪伴', summary: '人主笔 + P0 守门', active: current === 'companion' },
    { mode: 'advance', label: '推进', summary: '人定卷纲 + batch 产章', active: current === 'advance' },
    { mode: 'studio', label: '工作室', summary: '工厂流水线批量产章', active: current === 'studio' },
  ];
});

const creationModeGuideAnimationEnabled = computed(() => {
  if (!uiProfile.value.creation_mode_switch_guide_animation) return false;
  if (!uiProfile.value.creation_mode_switch_reduced_motion) return true;
  if (typeof window === 'undefined' || !window.matchMedia) return true;
  return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
});

const creationModeAccessibilityItems = computed(() => {
  if (!uiProfile.value.creation_mode_accessibility_checklist) return [];
  const profile = uiProfile.value;
  return [
    { id: 'hotkey', label: '快捷键 Alt+Shift+1/2/3', enabled: profile.creation_mode_switch_hotkey },
    { id: 'speech', label: '语音朗读', enabled: profile.creation_mode_switch_speech },
    { id: 'haptic', label: '触觉反馈', enabled: profile.creation_mode_switch_haptic },
    { id: 'aria', label: 'ARIA 公告', enabled: profile.creation_mode_switch_aria_live },
    { id: 'reduced', label: '减动画偏好', enabled: profile.creation_mode_switch_reduced_motion },
    { id: 'pinned', label: '固定侧栏', enabled: profile.creation_mode_preview_pinned_sidebar },
  ];
});

const creationModeCapabilityRows = computed(() => {
  if (!uiProfile.value.creation_mode_capability_matrix) return [];
  return CREATION_MODE_CAPABILITY_ROWS;
});

const pendingModeSwitchLabel = computed(() => {
  if (!pendingModeSwitch.value?.mode) return '';
  return CREATION_MODE_ONBOARDING_LABELS[pendingModeSwitch.value.mode] || pendingModeSwitch.value.mode;
});

const creationModeSwitchDocLinks = computed(() => {
  if (!uiProfile.value.creation_mode_switch_doc_link || !overview.value) return [];
  const mode = overview.value.creation_mode;
  const onboardingDoc = onboardingWizard.value?.onboarding_doc || 'docs/creator-onboarding.md';
  if (mode === 'companion') {
    return [
      { id: 'advance-checklist', label: '推进走通清单', path: 'docs/advance-walkthrough-checklist.md' },
      { id: 'onboarding', label: '模式说明', path: onboardingDoc },
    ];
  }
  if (mode === 'advance') {
    return [
      { id: 'companion-checklist', label: '陪伴走通清单', path: 'docs/companion-walkthrough-checklist.md' },
      { id: 'onboarding', label: '模式说明', path: onboardingDoc },
    ];
  }
  return [];
});

const studioCreationEntryHintText = computed(() => {
  if (!uiProfile.value.studio_creation_entry_hint || !overview.value) return '';
  if (overview.value.creation_mode === 'studio') {
    return '工作室模式：工厂流水线与批量产章。人主笔请设 creation_mode: companion，人定卷纲请设 creation_mode: advance';
  }
  return '';
});

const modeGuideExpanded = computed(
  () => !uiProfile.value.creator_mode_guide_default_collapsed,
);

const showModeGuidePanel = computed(
  () => isCreatorChromeVisible(overview.value?.creation_mode, 'modeGuide'),
);

function loadCreationModeSwitchHistory() {
  if (!uiProfile.value.creation_mode_switch_history) {
    creationModeSwitchHistory.value = [];
    return;
  }
  try {
    const raw = localStorage.getItem(CREATION_MODE_SWITCH_HISTORY_KEY);
    creationModeSwitchHistory.value = raw ? JSON.parse(raw) : [];
  } catch {
    creationModeSwitchHistory.value = [];
  }
}

function recordCreationModeSwitchHistory(mode, action) {
  if (!uiProfile.value.creation_mode_switch_history || !mode) return;
  const entry = {
    mode,
    label: CREATION_MODE_ONBOARDING_LABELS[mode] || mode,
    action,
    at: new Date().toISOString().slice(0, 19).replace('T', ' '),
  };
  const next = [
    entry,
    ...creationModeSwitchHistory.value.filter(
      (row) => !(row.mode === entry.mode && row.action === entry.action && row.at === entry.at),
    ),
  ].slice(0, 5);
  creationModeSwitchHistory.value = next;
  try {
    localStorage.setItem(CREATION_MODE_SWITCH_HISTORY_KEY, JSON.stringify(next));
  } catch {
    /* ignore storage errors */
  }
}

function maybeRecordModeSwitch(mode, action) {
  if (!mode || !overview.value || mode === overview.value.creation_mode) return;
  if (uiProfile.value.creation_mode_switch_undo_hint) {
    lastModeSwitchUndo.value = {
      fromMode: overview.value.creation_mode,
      fromLabel: CREATION_MODE_ONBOARDING_LABELS[overview.value.creation_mode] || overview.value.creation_mode,
      toMode: mode,
      toLabel: CREATION_MODE_ONBOARDING_LABELS[mode] || mode,
      action,
    };
  }
  recordCreationModeSwitchHistory(mode, action);
}

async function applyModeSwitchUndoHint() {
  if (!uiProfile.value.creation_mode_switch_undo_hint || !lastModeSwitchUndo.value) return;
  const snippet = `creation_mode: ${lastModeSwitchUndo.value.fromMode}`;
  try {
    await navigator.clipboard.writeText(snippet);
    saveMessage.value = `撤销提示：已复制 ${snippet}`;
  } catch {
    saveMessage.value = snippet;
  }
  lastModeSwitchUndo.value = null;
}

function requestCreationModeYaml(mode, active = false) {
  if (!uiProfile.value.creation_mode_yaml_snippet || !mode || active) {
    if (mode) copyCreationModeYaml(mode);
    return;
  }
  if (!uiProfile.value.creation_mode_switch_confirm_dialog) {
    copyCreationModeYaml(mode);
    return;
  }
  pendingModeSwitch.value = { mode, action: 'yaml' };
}

async function linkModeToOnboardingStepWithHistory(mode) {
  await linkModeToOnboardingStep(mode);
  maybeRecordModeSwitch(mode, '向导');
}

function requestOnboardingStepLink(mode, active = false) {
  if (!uiProfile.value.creation_mode_onboarding_step_link || !mode || active) {
    if (mode) linkModeToOnboardingStepWithHistory(mode);
    return;
  }
  if (!uiProfile.value.creation_mode_switch_confirm_dialog) {
    linkModeToOnboardingStepWithHistory(mode);
    return;
  }
  pendingModeSwitch.value = { mode, action: 'onboarding' };
}

function isEditableHotkeyTarget(target) {
  if (!target || typeof target !== 'object') return false;
  const tag = String(target.tagName || '').toLowerCase();
  return tag === 'input' || tag === 'textarea' || Boolean(target.isContentEditable);
}

function onCreationModeSwitchHotkey(event) {
  if (!uiProfile.value.creation_mode_switch_hotkey) return;
  if (!event.altKey || !event.shiftKey || event.ctrlKey || event.metaKey) return;
  const mode = CREATION_MODE_HOTKEY_MODES[event.key];
  if (!mode) return;
  if (isEditableHotkeyTarget(event.target)) return;
  event.preventDefault();
  const active = overview.value?.creation_mode === mode;
  requestCreationModeYaml(mode, active);
}

async function confirmCreationModeSwitch() {
  const pending = pendingModeSwitch.value;
  pendingModeSwitch.value = null;
  if (!pending?.mode) return;
  if (pending.action === 'onboarding') {
    await linkModeToOnboardingStep(pending.mode);
    maybeRecordModeSwitch(pending.mode, '向导');
    return;
  }
  await copyCreationModeYaml(pending.mode);
}

function cancelCreationModeSwitch() {
  pendingModeSwitch.value = null;
}

async function copyCreationModeYaml(mode) {
  if (!uiProfile.value.creation_mode_yaml_snippet || !mode) return;
  const snippet = `creation_mode: ${mode}`;
  try {
    await navigator.clipboard.writeText(snippet);
    saveMessage.value = `已复制：${snippet}`;
  } catch {
    saveMessage.value = snippet;
  }
  maybeRecordModeSwitch(mode, 'YAML');
  speakCreationModeSwitch(mode);
  triggerCreationModeSwitchHaptic();
  announceCreationModeSwitch(mode);
}

function announceCreationModeSwitch(mode) {
  if (!uiProfile.value.creation_mode_switch_aria_live || !mode) return;
  const label = CREATION_MODE_ONBOARDING_LABELS[mode] || mode;
  creationModeSwitchAriaMessage.value = `已请求切换至${label}模式`;
}

function triggerCreationModeSwitchHaptic() {
  if (!uiProfile.value.creation_mode_switch_haptic) return;
  try {
    navigator?.vibrate?.(15);
  } catch {
    // ignore unsupported environments
  }
}

function speakCreationModeSwitch(mode) {
  if (!uiProfile.value.creation_mode_switch_speech || !mode) return;
  if (typeof window === 'undefined' || !window.speechSynthesis) return;
  if (typeof SpeechSynthesisUtterance === 'undefined') return;
  const label = CREATION_MODE_ONBOARDING_LABELS[mode] || mode;
  const utterance = new SpeechSynthesisUtterance(`${label}模式，请设置 creation_mode 为 ${mode}`);
  utterance.lang = 'zh-CN';
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

function openModeSwitchDoc(link, fromClick = false) {
  if (!link?.path) return;
  if (uiProfile.value.creation_mode_switch_doc_open && fromClick) {
    try {
      window.open(link.path, '_blank', 'noopener');
    } catch {
      /* jsdom */
    }
    saveMessage.value = `已打开文档：${link.path}`;
    return;
  }
  saveMessage.value = `文档：${link.path}`;
}

const panelContext = {
  uiProfile,
  modeLabel,
  modeGuideExpanded,
  showModeGuidePanel,
  creationModeSwitchHintText,
  creationModeSwitchDocLinks,
  creationModeSwitchAriaMessage,
  creationModePreviewRows,
  creationModeGuideAnimationEnabled,
  pendingModeSwitch,
  pendingModeSwitchLabel,
  creationModeSwitchHistory,
  lastModeSwitchUndo,
  creationModeAccessibilityItems,
  creationModeCapabilityRows,
  studioCreationEntryHintText,
  openModeSwitchDoc,
  requestCreationModeYaml,
  requestOnboardingStepLink,
  confirmCreationModeSwitch,
  cancelCreationModeSwitch,
  applyModeSwitchUndoHint,
};

return {
  panelContext,
  loadCreationModeSwitchHistory,
  onCreationModeSwitchHotkey,
};
}
