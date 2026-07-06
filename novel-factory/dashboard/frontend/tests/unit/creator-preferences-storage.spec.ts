import { describe, it, expect, beforeEach } from 'vitest';
import {
  defaultCreatorPreferences,
  loadCreatorPreferences,
  saveCreatorPreferences,
  mergeCreatorPreferences,
  resolveTaskModel,
  CREATOR_PREFERENCES_STORAGE_KEY,
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

  it('resolveTaskModel inherits default', () => {
    const prefs = defaultCreatorPreferences();
    expect(resolveTaskModel('body', prefs)).toBe(prefs.defaultModel);
    prefs.taskModels.body = 'gpt-4o';
    expect(resolveTaskModel('body', prefs)).toBe('gpt-4o');
  });
});
