import { describe, it, expect } from 'vitest';
import { preferencesFromApi, preferencesToApi } from '../../src/utils/creatorPreferencesApi.js';
import { defaultCreatorPreferences } from '../../src/utils/creatorPreferencesStorage.js';

describe('creatorPreferencesApi', () => {
  it('preferencesFromApi maps snake_case', () => {
    const prefs = preferencesFromApi({
      default_model: 'gpt-4o',
      temperature: 0.5,
      max_tokens: 4000,
      memory_rag_enabled: false,
      memory_rag_top_k: 3,
      task_models: { body: 'claude-sonnet' },
      companion_lightweight: false,
    });
    expect(prefs.defaultModel).toBe('gpt-4o');
    expect(prefs.taskModels.body).toBe('claude-sonnet');
    expect(prefs.memoryRagEnabled).toBe(false);
  });

  it('preferencesToApi maps camelCase', () => {
    const base = defaultCreatorPreferences();
    const api = preferencesToApi({ ...base, temperature: 0.9 });
    expect(api.temperature).toBe(0.9);
    expect(api.default_model).toBe(base.defaultModel);
    expect((api.intervention_rules as Record<string, boolean>).logic_p0).toBe(true);
  });

  it('preferencesFromApi returns defaults for empty payload', () => {
    const prefs = preferencesFromApi(null as unknown as Record<string, unknown>);
    expect(prefs.defaultModel).toBe(defaultCreatorPreferences().defaultModel);
  });

  it('preferencesToApi maps all intervention rules', () => {
    const base = defaultCreatorPreferences();
    const api = preferencesToApi({
      ...base,
      interventionRules: { ...base.interventionRules, batchProgress: false, memoryOffline: false },
    });
    const rules = api.intervention_rules as Record<string, boolean>;
    expect(rules.batch_progress).toBe(false);
    expect(rules.memory_offline).toBe(false);
    expect(rules.logic_p0).toBe(true);
  });
});
