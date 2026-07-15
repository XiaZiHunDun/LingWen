/**
 * 创作偏好 localStorage（前端先行，后端可后接同步）
 */

export const CREATOR_PREFERENCES_STORAGE_KEY = 'lingwen.creator.preferences.v1';

export const CREATOR_MODEL_OPTIONS = [
  { id: 'minimax-abab6.5', label: 'MiniMax abab6.5' },
  { id: 'claude-sonnet', label: 'Claude Sonnet' },
  { id: 'gpt-4o', label: 'GPT-4o' },
  { id: 'local-mock', label: '本地 Mock（开发）' },
];

export const CREATOR_TASK_KEYS = [
  { id: 'outline', label: '大纲 / 卷纲' },
  { id: 'body', label: '正文写作' },
  { id: 'review', label: '逻辑审查' },
  { id: 'memory', label: '记忆整理' },
];

export const CREATOR_INTERVENTION_RULE_KEYS = [
  { id: 'deviationAlerts', apiKey: 'deviation_alerts', label: '偏离需关注' },
  { id: 'batchProgress', apiKey: 'batch_progress', label: '批量推进进行中' },
  { id: 'logicP0', apiKey: 'logic_p0', label: 'P0 逻辑问题' },
  { id: 'settingsUnsaved', apiKey: 'settings_unsaved', label: '设定未保存' },
  { id: 'preferencesUnsaved', apiKey: 'preferences_unsaved', label: '偏好未保存' },
  { id: 'memoryOffline', apiKey: 'memory_offline', label: '记忆系统离线' },
  { id: 'emptyWriteHint', apiKey: 'empty_write_hint', label: '尚未开始写作提示' },
];

/** @returns {import('./creatorPreferencesStorage.js').CreatorInterventionRules} */
export function defaultInterventionRules() {
  return {
    deviationAlerts: true,
    batchProgress: true,
    logicP0: true,
    settingsUnsaved: true,
    preferencesUnsaved: true,
    memoryOffline: true,
    emptyWriteHint: true,
  };
}

/** @returns {import('./creatorPreferencesStorage.js').CreatorPreferences} */
export function defaultCreatorPreferences() {
  return {
    defaultModel: 'minimax-abab6.5',
    temperature: 0.7,
    maxTokens: 8000,
    memoryRagEnabled: true,
    memoryRagTopK: 8,
    taskModels: {
      outline: 'inherit',
      body: 'inherit',
      review: 'inherit',
      memory: 'inherit',
    },
    companionLightweight: true,
    interventionRules: defaultInterventionRules(),
  };
}

/**
 * @typedef {ReturnType<typeof defaultCreatorPreferences>} CreatorPreferences
 */

/** @param {Partial<CreatorPreferences>} patch */
export function mergeCreatorPreferences(patch) {
  const base = defaultCreatorPreferences();
  return {
    ...base,
    ...patch,
    taskModels: { ...base.taskModels, ...(patch.taskModels || {}) },
    interventionRules: {
      ...base.interventionRules,
      ...(patch.interventionRules || {}),
    },
  };
}

/** @returns {CreatorPreferences} */
export function loadCreatorPreferences() {
  if (typeof localStorage === 'undefined') return defaultCreatorPreferences();
  try {
    const raw = localStorage.getItem(CREATOR_PREFERENCES_STORAGE_KEY);
    if (!raw) return defaultCreatorPreferences();
    return mergeCreatorPreferences(JSON.parse(raw));
  } catch {
    return defaultCreatorPreferences();
  }
}

/** @param {CreatorPreferences} prefs */
export function saveCreatorPreferences(prefs) {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(CREATOR_PREFERENCES_STORAGE_KEY, JSON.stringify(prefs));
}

/** @param {string} taskId @param {CreatorPreferences} prefs */
export function resolveTaskModel(taskId, prefs) {
  const taskModel = prefs.taskModels?.[taskId];
  if (!taskModel || taskModel === 'inherit') return prefs.defaultModel;
  return taskModel;
}
