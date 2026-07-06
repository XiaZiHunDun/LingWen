/**
 * 创作者前端面板矩阵（Capability Matrix → 面板级布局）
 *
 * 优先级语义：
 * - required          — 必显（主路径）
 * - optional          — 显式入口，默认展开
 * - optional_collapsed— 显式入口，默认折叠（<details> / 高级区）
 * - hidden            — 不渲染（仍可通过 URL / ui_profile 强制开启的除外）
 *
 * 模式：companion（陪伴）| advance（推进）| studio（工厂）
 */
import { resolveNavCreationMode } from './dashboardNavByMode.js';

/** @typedef {'required'|'optional'|'optional_collapsed'|'hidden'} PanelPriority */

/** @type {{ id: string, label: string, icon?: string }[]} */
export const CREATOR_WORKSPACE_TAB_DEFS = [
  { id: 'write', label: '写作' },
  { id: 'pulse', label: '脉络' },
  { id: 'memory', label: '记忆' },
  { id: 'settings', label: '本书设定' },
];

/**
 * Dashboard Hub 侧栏（与 dashboardNavByMode 对齐，文档用）
 * @type {Record<string, Record<string, PanelPriority>>}
 */
export const DASHBOARD_HUB_MATRIX = {
  today: { companion: 'required', advance: 'required', studio: 'required' },
  creator: { companion: 'required', advance: 'required', studio: 'hidden' },
  produce: { companion: 'hidden', advance: 'required', studio: 'required' },
  inbox: { companion: 'required', advance: 'required', studio: 'required' },
  insight: { companion: 'optional', advance: 'optional', studio: 'optional' },
  'cascade-runs': { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'optional_collapsed' },
  settings: { companion: 'optional', advance: 'optional', studio: 'optional' },
};

/**
 * 创作页工作区 Tab
 * @type {Record<string, Record<string, PanelPriority>>}
 */
export const CREATOR_WORKSPACE_TAB_MATRIX = {
  write: { companion: 'required', advance: 'required', studio: 'hidden' },
  pulse: { companion: 'optional', advance: 'optional', studio: 'required' },
  memory: { companion: 'optional', advance: 'optional_collapsed', studio: 'optional' },
  settings: { companion: 'required', advance: 'optional_collapsed', studio: 'optional_collapsed' },
};

/** 人类习惯书桌：记忆/设定收进次要 Tab 行 */
export const HUMAN_FIRST_DESK_SECONDARY_TAB_IDS = ['memory', 'settings'];

/** @type {Record<string, string>} */
export const CREATOR_WORKSPACE_DEFAULT_TAB = {
  companion: 'write',
  advance: 'write',
  studio: 'pulse',
};

/**
 * 脉络栏子面板
 * @type {Record<string, Record<string, PanelPriority>>}
 */
export const CREATOR_PULSE_SUBPANEL_MATRIX = {
  structureGraph: { companion: 'optional_collapsed', advance: 'required', studio: 'required' },
  volumePulse: { companion: 'optional_collapsed', advance: 'required', studio: 'required' },
  volumePlan: { companion: 'optional_collapsed', advance: 'required', studio: 'required' },
  deviationList: { companion: 'optional', advance: 'required', studio: 'required' },
  advanceBatch: { companion: 'hidden', advance: 'required', studio: 'hidden' },
  batchHistory: { companion: 'hidden', advance: 'optional', studio: 'optional' },
  volumeSummaries: { companion: 'optional', advance: 'optional', studio: 'optional' },
};

/**
 * 创作页外围面板（工作区下方 / 弹窗）
 * @type {Record<string, Record<string, PanelPriority>>}
 */
export const CREATOR_CHROME_MATRIX = {
  modeGuide: { companion: 'hidden', advance: 'optional_collapsed', studio: 'optional_collapsed' },
  onboardingWizard: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'optional_collapsed' },
  exportModal: { companion: 'optional', advance: 'required', studio: 'required' },
  publishWizard: { companion: 'optional', advance: 'optional', studio: 'optional' },
  interventionBanner: { companion: 'required', advance: 'required', studio: 'optional' },
};

/**
 * 生产 Hub 子 Tab（用户已进入生产页时）
 * @type {Record<string, Record<string, PanelPriority>>}
 */
export const HUB_PRODUCE_TAB_MATRIX = {
  studio: { companion: 'hidden', advance: 'required', studio: 'required' },
  chapters: { companion: 'hidden', advance: 'optional', studio: 'required' },
  workflows: { companion: 'hidden', advance: 'optional', studio: 'optional' },
};

/**
 * 写栏工作台布局（左栈 + 右编辑器）— Human Comfort P0
 * @type {Record<string, Record<string, PanelPriority>>}
 */
export const CREATOR_WRITE_WORKBENCH_MATRIX = {
  workbenchLayout: { companion: 'required', advance: 'required', studio: 'hidden' },
  goalCard: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'hidden' },
  intentInput: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'hidden' },
  selectionRewriteToolbar: { companion: 'required', advance: 'optional', studio: 'hidden' },
  generateToolbar: { companion: 'required', advance: 'optional', studio: 'hidden' },
  agentSessionStrip: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'hidden' },
  candidatePreviewDock: { companion: 'required', advance: 'optional', studio: 'hidden' },
  qualityFeedbackBar: { companion: 'optional_collapsed', advance: 'optional', studio: 'hidden' },
  versionCheckpointList: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'hidden' },
  chapterTaskCards: { companion: 'hidden', advance: 'optional_collapsed', studio: 'required' },
  scopeBar: { companion: 'required', advance: 'optional', studio: 'hidden' },
  directorPaths: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'hidden' },
  controlStrip: { companion: 'required', advance: 'optional', studio: 'hidden' },
  consistencyRail: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'hidden' },
  checkpointDiff: { companion: 'required', advance: 'required', studio: 'hidden' },
  chapterEntityRail: { companion: 'optional_collapsed', advance: 'optional_collapsed', studio: 'hidden' },
  inlineConflictGutter: { companion: 'required', advance: 'optional', studio: 'hidden' },
  agentLensSwitcher: { companion: 'required', advance: 'optional', studio: 'hidden' },
};

/**
 * Human Comfort 六维权重（high / medium / low）— 排期与 PRD 用
 * @type {Record<string, Record<string, 'high'|'medium'|'low'>>}
 */
export const COMFORT_DIMENSION_WEIGHTS = {
  lowBurdenInput: { companion: 'high', advance: 'medium', studio: 'low' },
  instantFeedback: { companion: 'high', advance: 'medium', studio: 'low' },
  rhythmOrchestration: { companion: 'low', advance: 'high', studio: 'high' },
  qualityAssist: { companion: 'medium', advance: 'high', studio: 'high' },
  assetTracking: { companion: 'medium', advance: 'high', studio: 'high' },
  cognitiveLoad: { companion: 'high', advance: 'medium', studio: 'medium' },
};

/** Agent 默认执行模式 */
export const AGENT_EXECUTION_MODES = {
  preview: 'preview',
  apply: 'apply',
};

/** 风格强度：0=只建议不改写，3=全段改写 */
export const STYLE_STRENGTH_LEVELS = [
  { level: 0, label: '只建议' },
  { level: 1, label: '轻改' },
  { level: 2, label: '改写' },
  { level: 3, label: '代写' },
];

/** 写作目标标签（绑定 prompt 模板） */
export const AGENT_GOAL_TAGS = [
  { id: 'suspense', label: '悬疑' },
  { id: 'pace', label: '节奏' },
  { id: 'restraint', label: '克制' },
  { id: 'conflict', label: '冲突' },
];

/** Agent 透镜（改变结果呈现与 prompt 侧重） */
export const AGENT_LENS_MODES = [
  { id: 'author', label: '作者' },
  { id: 'editor', label: '编辑' },
  { id: 'reviewer', label: '审稿' },
  { id: 'polish', label: '打磨' },
  { id: 'roleplay', label: '角色' },
];

/**
 * 三模式能力对照行（供模式说明表复用）
 */
export const CREATION_MODE_CAPABILITY_ROWS = [
  { id: 'human-writing', label: '人主笔', companion: true, advance: false, studio: false },
  { id: 'p0-guard', label: 'P0 守门', companion: true, advance: false, studio: false },
  { id: 'inline-chapter-edit', label: '章内嵌编辑', companion: true, advance: false, studio: false },
  { id: 'volume-plan-edit', label: '卷纲编辑', companion: true, advance: true, studio: false },
  { id: 'volume-pulse', label: '脉络预警', companion: false, advance: true, studio: true },
  { id: 'batch-generate', label: 'Batch 产章', companion: false, advance: true, studio: true },
  { id: 'factory-pipeline', label: '工厂流水线', companion: false, advance: false, studio: true },
  { id: 'digest-ops', label: 'Digest 运维', companion: false, advance: false, studio: true },
];

/**
 * 模式级 ui_profile 默认值（服务端未显式覆盖时生效）
 * @type {Record<string, Record<string, unknown>>}
 */
export const MODE_UI_PROFILE_DEFAULTS = {
  companion: {
    creator_mode_guide_default_collapsed: true,
    creator_simplified_mode_ops: true,
    creator_write_workbench: true,
    primary_action: 'logic_check',
    volume_pulse_enabled: false,
    show_studio_workflow: false,
    agent_execution_mode_default: 'preview',
    write_inline_conflict_gutter: true,
    write_chapter_entity_rail: true,
    agent_lens_default: 'author',
    wizard_default_collapsed: true,
  },
  advance: {
    creator_mode_guide_default_collapsed: true,
    creator_simplified_mode_ops: true,
    creator_write_workbench: true,
    chapter_inline_edit: true,
    chapter_outline_inline_edit: true,
    chapter_full_preview: false,
    volume_pulse_enabled: true,
    advance_batch_panel_on_creator: true,
    agent_execution_mode_default: 'preview',
    write_inline_conflict_gutter: true,
    write_chapter_entity_rail: true,
    agent_lens_default: 'author',
    wizard_default_collapsed: true,
  },
  studio: {
    creator_mode_guide_default_collapsed: true,
    creator_write_workbench: false,
    show_studio_workflow: true,
    volume_pulse_enabled: true,
  },
};

/**
 * @param {string | null | undefined} mode
 */
export function resolveCreationMode(mode) {
  return resolveNavCreationMode(mode);
}

/**
 * @param {Record<string, Record<string, PanelPriority>>} matrix
 * @param {string | null | undefined} creationMode
 * @param {string} panelId
 * @returns {PanelPriority}
 */
export function getPanelPriority(matrix, creationMode, panelId) {
  const mode = resolveCreationMode(creationMode);
  const row = matrix[panelId];
  if (!row) return 'optional';
  return row[mode] ?? row.companion ?? 'optional';
}

/**
 * @param {Record<string, Record<string, PanelPriority>>} matrix
 * @param {string | null | undefined} creationMode
 * @param {string} panelId
 */
export function isPanelVisible(matrix, creationMode, panelId) {
  return getPanelPriority(matrix, creationMode, panelId) !== 'hidden';
}

/**
 * @param {Record<string, Record<string, PanelPriority>>} matrix
 * @param {string | null | undefined} creationMode
 * @param {string} panelId
 */
export function isPanelDefaultCollapsed(matrix, creationMode, panelId) {
  return getPanelPriority(matrix, creationMode, panelId) === 'optional_collapsed';
}

/**
 * @param {string | null | undefined} creationMode
 * @param {{ forceAllTabs?: boolean }} [options]
 */
export function buildCreatorWorkspaceTabs(creationMode, options = {}) {
  if (options.forceAllTabs) return [...CREATOR_WORKSPACE_TAB_DEFS];
  return CREATOR_WORKSPACE_TAB_DEFS.filter((tab) =>
    isPanelVisible(CREATOR_WORKSPACE_TAB_MATRIX, creationMode, tab.id),
  );
}

/**
 * @param {string | null | undefined} creationMode
 */
export function resolveDefaultWorkspaceTab(creationMode) {
  const mode = resolveCreationMode(creationMode);
  const preferred = CREATOR_WORKSPACE_DEFAULT_TAB[mode] || 'write';
  if (isPanelVisible(CREATOR_WORKSPACE_TAB_MATRIX, creationMode, preferred)) {
    return preferred;
  }
  const first = buildCreatorWorkspaceTabs(creationMode)[0];
  return first?.id || 'write';
}

/**
 * @param {string | null | undefined} creationMode
 * @param {string} subpanelId
 */
export function isPulseSubpanelVisible(creationMode, subpanelId) {
  return isPanelVisible(CREATOR_PULSE_SUBPANEL_MATRIX, creationMode, subpanelId);
}

/**
 * @param {string | null | undefined} creationMode
 * @param {string} chromeId
 */
export function isCreatorChromeVisible(creationMode, chromeId) {
  return isPanelVisible(CREATOR_CHROME_MATRIX, creationMode, chromeId);
}

/**
 * @param {string | null | undefined} creationMode
 */
export function getModeUiProfileDefaults(creationMode) {
  const mode = resolveCreationMode(creationMode);
  return { ...(MODE_UI_PROFILE_DEFAULTS[mode] || {}) };
}

/**
 * @param {string | null | undefined} creationMode
 * @param {string} tabId
 */
export function isHubProduceTabVisible(creationMode, tabId) {
  return isPanelVisible(HUB_PRODUCE_TAB_MATRIX, creationMode, tabId);
}

/**
 * @param {string | null | undefined} creationMode
 * @param {string} panelId
 */
export function isWriteWorkbenchPanelVisible(creationMode, panelId) {
  return isPanelVisible(CREATOR_WRITE_WORKBENCH_MATRIX, creationMode, panelId);
}

/**
 * @param {string | null | undefined} creationMode
 * @param {object} [uiProfile]
 */
export function isWriteWorkbenchLayoutEnabled(creationMode, uiProfile = {}) {
  if (uiProfile.creator_write_workbench === false) return false;
  if (uiProfile.creator_write_workbench === true) return true;
  return isWriteWorkbenchPanelVisible(creationMode, 'workbenchLayout');
}

/**
 * @param {string | null | undefined} creationMode
 */
export function isChapterTaskCardsVisible(creationMode) {
  return isWriteWorkbenchPanelVisible(creationMode, 'chapterTaskCards');
}

/**
 * @param {string | null | undefined} creationMode
 */
export function isHumanFirstDeskMode(creationMode) {
  const mode = resolveCreationMode(creationMode);
  return mode === 'companion' || mode === 'advance';
}

/**
 * @param {string | null | undefined} creationMode
 */
export function splitHumanFirstDeskTabs(creationMode) {
  const tabs = buildCreatorWorkspaceTabs(creationMode);
  if (!isHumanFirstDeskMode(creationMode)) {
    return { primary: tabs, secondary: [] };
  }
  const primary = tabs.filter((t) => !HUMAN_FIRST_DESK_SECONDARY_TAB_IDS.includes(t.id));
  const secondary = tabs.filter((t) => HUMAN_FIRST_DESK_SECONDARY_TAB_IDS.includes(t.id));
  return { primary, secondary };
}
