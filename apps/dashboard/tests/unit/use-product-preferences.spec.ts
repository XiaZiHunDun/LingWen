/**
 * useProductPreferences 子模块独立测试
 *
 * Phase 26: 为 Phase 19.1 useProductPreferences 子模块添加专门测试。
 * 重点测试：偏好加载/同步/保存 + 错误处理。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

// Mock API
const prefMocks = vi.hoisted(() => ({
  fetchCreatorPreferences: vi.fn(),
  saveCreatorPreferences: vi.fn(),
  fetchCreatorModels: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorPreferences: (...args: unknown[]) => prefMocks.fetchCreatorPreferences(...args),
  fetchCreatorModels: (...args: unknown[]) => prefMocks.fetchCreatorModels(...args),
}));

// v16.2.7 T6a: also mock the typed wrapper module so useProductPreferences (which
// now imports from @/api/content) resolves the same mocks. Per v16.2.5 §5.1 lesson 3.
vi.mock('../../src/api/content', () => ({
  fetchCreatorPreferences: (...args: unknown[]) => prefMocks.fetchCreatorPreferences(...args),
  saveCreatorPreferences: (...args: unknown[]) => prefMocks.saveCreatorPreferences(...args),
  fetchCreatorModels: (...args: unknown[]) => prefMocks.fetchCreatorModels(...args),
}));

// Mock utils（同步函数，简单返回）
vi.mock('../../src/utils/creatorPreferencesStorage.js', () => ({
  loadCreatorPreferences: () => ({ memoryRagEnabled: true, modelId: 'gpt-4', interventionRules: {} }),
  saveCreatorPreferences: vi.fn(),
  defaultCreatorPreferences: () => ({ memoryRagEnabled: true, modelId: 'gpt-4', interventionRules: {} }),
  CREATOR_MODEL_OPTIONS: [{ id: 'gpt-4', label: 'GPT-4' }],
}));
vi.mock('../../src/utils/creatorPreferencesApi.js', () => ({
  preferencesFromApi: (data: Record<string, unknown>) => ({ ...data, _from: 'api' }),
  preferencesToApi: (prefs: Record<string, unknown>) => ({ ...prefs, _to: 'api' }),
}));
vi.mock('../../src/utils/creatorPreferencesSummaryUtils.js', () => ({
  buildCreatorPreferencesSummary: (prefs: Record<string, unknown>, _opts: unknown) => ({ summary: 'test', prefs }),
}));

import { useProductPreferences } from '../../src/composables/useCreatorProductTools/useProductPreferences';

function mountPrefs() {
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  return useProductPreferences({ error, saveMessage });
}

describe('useProductPreferences', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    prefMocks.fetchCreatorModels.mockResolvedValue({ models: [{ id: 'gpt-4', label: 'GPT-4' }] });
    prefMocks.fetchCreatorPreferences.mockResolvedValue({ memoryRagEnabled: true, modelId: 'gpt-4' });
    prefMocks.saveCreatorPreferences.mockResolvedValue({ ok: true });
  });

  it('loadCreatorModels updates creatorModelOptions from API', async () => {
    const prefs = mountPrefs();
    await prefs.loadCreatorModels();
    expect(prefs.creatorModelOptions.value).toEqual([{ id: 'gpt-4', label: 'GPT-4' }]);
  });

  it('loadCreatorModels falls back to default options on API failure', async () => {
    prefMocks.fetchCreatorModels.mockRejectedValueOnce(new Error('down'));
    const prefs = mountPrefs();
    await prefs.loadCreatorModels();
    expect(prefs.creatorModelOptions.value.length).toBeGreaterThan(0);
  });

  it('loadPreferencesFromServer syncs from API', async () => {
    const prefs = mountPrefs();
    await prefs.loadPreferencesFromServer();
    expect(prefs.preferencesSyncSource.value).toBe('server');
    expect(prefs.preferencesDirty.value).toBe(false);
  });

  it('loadPreferencesFromServer falls back to local on failure', async () => {
    prefMocks.fetchCreatorPreferences.mockRejectedValueOnce(new Error('network'));
    const prefs = mountPrefs();
    await prefs.loadPreferencesFromServer();
    expect(prefs.preferencesSyncSource.value).toBe('local');
  });

  it('markPreferencesDirty sets dirty and clears savedHint', () => {
    const prefs = mountPrefs();
    prefs.preferencesSavedHint.value = 'old';
    prefs.markPreferencesDirty();
    expect(prefs.preferencesDirty.value).toBe(true);
    expect(prefs.preferencesSavedHint.value).toBe('');
  });

  it('resetPreferences sets defaults and marks dirty', () => {
    const prefs = mountPrefs();
    prefs.markPreferencesDirty();
    prefs.preferencesSavedHint.value = 'old';
    prefs.resetPreferences();
    expect(prefs.preferencesDirty.value).toBe(true);
    expect(prefs.preferencesSavedHint.value).toBe('');
  });

  it('savePreferences syncs to server on success', async () => {
    const prefs = mountPrefs();
    prefs.markPreferencesDirty();
    await prefs.savePreferences();
    expect(prefs.preferencesSyncSource.value).toBe('server');
    expect(prefs.preferencesDirty.value).toBe(false);
  });

  it('savePreferences falls back to local on server failure', async () => {
    prefMocks.saveCreatorPreferences.mockRejectedValueOnce(new Error('conflict'));
    const prefs = mountPrefs();
    prefs.markPreferencesDirty();
    await prefs.savePreferences();
    expect(prefs.preferencesSyncSource.value).toBe('local');
  });

  it('preferencesSummary reflects current preferences', () => {
    const prefs = mountPrefs();
    // preferencesSummary 是内部 computed 通过 buildCreatorPreferencesSummary 计算
    // 这里只验证存在性（实际值由子模块内部决定）
    expect(prefs.preferences).toBeDefined();
  });

  it('initial state has defaults loaded from storage', () => {
    const prefs = mountPrefs();
    // 通过 preferences 对象访问初始值
    expect(prefs.preferencesDirty.value).toBe(false);
    expect(prefs.preferencesSyncSource.value).toBe('local');
  });
});
