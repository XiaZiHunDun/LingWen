import { describe, it, expect, beforeEach } from 'vitest';
import {
  defaultCreatorPreferences,
  loadCreatorPreferences,
  saveCreatorPreferences,
  mergeCreatorPreferences,
  resolveTaskModel,
  CREATOR_PREFERENCES_STORAGE_KEY,
  defaultInterventionRules,
} from '../../src/utils/creatorPreferencesStorage.js';

describe('creatorPreferencesStorage', () => {
  beforeEach(() => {
    localStorage.removeItem(CREATOR_PREFERENCES_STORAGE_KEY);
  });

  it('defaultCreatorPreferences has expected shape', () => {
    const prefs = defaultCreatorPreferences();
    expect(prefs.defaultModel).toBeTruthy();
    expect(prefs.taskModels.body).toBe('inherit');
  });

  it('save and load roundtrip', () => {
    const prefs = mergeCreatorPreferences({ temperature: 0.3 });
    saveCreatorPreferences(prefs);
    const loaded = loadCreatorPreferences();
    expect(loaded.temperature).toBe(0.3);
  });

  it('loadCreatorPreferences returns defaults for corrupt JSON', () => {
    localStorage.setItem(CREATOR_PREFERENCES_STORAGE_KEY, '{not-json');
    expect(loadCreatorPreferences().defaultModel).toBe(defaultCreatorPreferences().defaultModel);
  });

  it('mergeCreatorPreferences deep-merges intervention rules', () => {
    const merged = mergeCreatorPreferences({
      interventionRules: { logicP0: false },
    });
    expect(merged.interventionRules.logicP0).toBe(false);
    expect(merged.interventionRules.batchProgress).toBe(defaultInterventionRules().batchProgress);
  });

  it('resolveTaskModel falls back when task model missing', () => {
    const prefs = defaultCreatorPreferences();
    prefs.taskModels.outline = '';
    expect(resolveTaskModel('outline', prefs)).toBe(prefs.defaultModel);
  });
});
