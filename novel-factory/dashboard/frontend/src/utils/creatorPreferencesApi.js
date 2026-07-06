/**
 * API ↔ localStorage 创作偏好字段转换
 */
import {
  defaultCreatorPreferences,
  defaultInterventionRules,
  mergeCreatorPreferences,
  CREATOR_INTERVENTION_RULE_KEYS,
} from './creatorPreferencesStorage.js';

/** @param {Record<string, boolean>|undefined} apiRules */
function interventionRulesFromApi(apiRules) {
  const base = defaultInterventionRules();
  if (!apiRules || typeof apiRules !== 'object') return base;
  const out = { ...base };
  for (const row of CREATOR_INTERVENTION_RULE_KEYS) {
    if (row.apiKey in apiRules) {
      out[row.id] = Boolean(apiRules[row.apiKey]);
    }
  }
  return out;
}

/** @param {import('./creatorPreferencesStorage.js').CreatorInterventionRules} rules */
function interventionRulesToApi(rules) {
  const out = {};
  for (const row of CREATOR_INTERVENTION_RULE_KEYS) {
    out[row.apiKey] = Boolean(rules?.[row.id]);
  }
  return out;
}

/** @param {Record<string, unknown>} api */
export function preferencesFromApi(api) {
  if (!api) return defaultCreatorPreferences();
  return mergeCreatorPreferences({
    defaultModel: api.default_model,
    temperature: api.temperature,
    maxTokens: api.max_tokens,
    memoryRagEnabled: api.memory_rag_enabled,
    memoryRagTopK: api.memory_rag_top_k,
    taskModels: api.task_models,
    companionLightweight: api.companion_lightweight,
    interventionRules: interventionRulesFromApi(api.intervention_rules),
  });
}

/** @param {import('./creatorPreferencesStorage.js').CreatorPreferences} prefs */
export function preferencesToApi(prefs) {
  return {
    default_model: prefs.defaultModel,
    temperature: prefs.temperature,
    max_tokens: prefs.maxTokens,
    memory_rag_enabled: prefs.memoryRagEnabled,
    memory_rag_top_k: prefs.memoryRagTopK,
    task_models: prefs.taskModels,
    companion_lightweight: prefs.companionLightweight,
    intervention_rules: interventionRulesToApi(prefs.interventionRules),
  };
}
