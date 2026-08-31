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

/**
 * Convert API response to local `CreatorPreferences` shape.
 *
 * v16.5 #N.13 T2.P1.a: accept either the canonical `CreatorPreferencesResponse`
 * DTO (new shape: `creation_mode`, `quality_profile`, etc.) OR the legacy
 * snake_case shape (`default_model`, `temperature`, etc.). The legacy fields are
 * not in the new DTO; if absent, `mergeCreatorPreferences` falls back to local
 * defaults. JSDoc widened to `object` so callers (e.g. `useProductPreferences.ts`)
 * can pass `CreatorPreferencesResponse` without an `as unknown as` cast; an
 * internal `Record<string, any>` JSDoc cast inside the body keeps property
 * access permissive.
 *
 * @param {object} api - Either typed DTO or legacy snake_case object.
 */
export function preferencesFromApi(api) {
  if (!api) return defaultCreatorPreferences();
  /** @type {Record<string, any>} */
  const snake = api;
  return mergeCreatorPreferences({
    defaultModel: snake.default_model,
    temperature: snake.temperature,
    maxTokens: snake.max_tokens,
    memoryRagEnabled: snake.memory_rag_enabled,
    memoryRagTopK: snake.memory_rag_top_k,
    taskModels: snake.task_models,
    companionLightweight: snake.companion_lightweight,
    interventionRules: interventionRulesFromApi(snake.intervention_rules),
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
