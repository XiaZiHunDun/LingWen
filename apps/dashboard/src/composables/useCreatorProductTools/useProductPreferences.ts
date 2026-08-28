/**
 * useProductPreferences — 创作偏好、模型、同步状态
 *
 * Phase 19 Task 1.4：从 useCreatorProductTools.js 拆出，最终接入。
 * 负责: preferences state + 模型加载 + 服务端同步。
 *
 * 依赖 (deps):
 * - error: 用于报错信息回写
 * - saveMessage: 用于顶部消息提示
 *
 * 注: 不计算 preferencesSummary（依赖 memoryRagEnabled，循环依赖）—— 在主 hook 组合。
 */
import { ref } from 'vue';
import type { Ref } from 'vue';
import {
  fetchCreatorPreferences,
  saveCreatorPreferences,
  fetchCreatorModels,
} from '@/api/content';
import {
  loadCreatorPreferences,
  saveCreatorPreferences as saveCreatorPreferencesLocal,
  defaultCreatorPreferences,
  CREATOR_MODEL_OPTIONS,
} from '../../utils/creatorPreferencesStorage.js';
import { preferencesFromApi, preferencesToApi } from '../../utils/creatorPreferencesApi.js';

type PreferencesShape = ReturnType<typeof loadCreatorPreferences>;

export interface PreferencesDeps {
  error: Ref<string | null>;
  saveMessage: Ref<string>;
}

export interface ProductPreferencesReturn {
  preferences: Ref<PreferencesShape>;
  preferencesDirty: Ref<boolean>;
  preferencesSavedHint: Ref<string>;
  preferencesSyncSource: Ref<string>;
  creatorModelOptions: Ref<Array<{ id: string; label: string }>>;
  loadCreatorModels: () => Promise<void>;
  loadPreferencesFromServer: () => Promise<void>;
  markPreferencesDirty: () => void;
  resetPreferences: () => void;
  savePreferences: () => Promise<void>;
}

export function useProductPreferences(deps: PreferencesDeps): ProductPreferencesReturn {
  const { error, saveMessage } = deps;

  const preferences = ref(loadCreatorPreferences()) as Ref<PreferencesShape>;
  const preferencesDirty = ref(false);
  const preferencesSavedHint = ref('');
  const preferencesSyncSource = ref('local');
  const creatorModelOptions = ref([...CREATOR_MODEL_OPTIONS]);

  async function loadCreatorModels(): Promise<void> {
    try {
      // v16.2.7 T8: typed wrapper's CreatorModelsResponse is strict-typed;
      // legacy shape used loose Record<string, unknown>. Cast preserves behavior.
      const data = await fetchCreatorModels() as unknown as { models?: Array<{ id: string; label: string }> };
      if (data.models?.length) {
        creatorModelOptions.value = data.models;
      }
    } catch {
      creatorModelOptions.value = [...CREATOR_MODEL_OPTIONS];
    }
  }

  async function loadPreferencesFromServer(): Promise<void> {
    try {
      // v16.2.7 T8: typed wrapper response doesn't match preferencesFromApi
      // signature (Record<string, unknown>); cast preserves legacy behavior.
      const data = await fetchCreatorPreferences() as unknown as Record<string, unknown>;
      preferences.value = preferencesFromApi(data);
      saveCreatorPreferencesLocal(preferences.value);
      preferencesSyncSource.value = 'server';
      preferencesDirty.value = false;
    } catch {
      preferences.value = loadCreatorPreferences();
      preferencesSyncSource.value = 'local';
    }
  }

  function markPreferencesDirty(): void {
    preferencesDirty.value = true;
    preferencesSavedHint.value = '';
  }

  function resetPreferences(): void {
    preferences.value = defaultCreatorPreferences();
    preferencesDirty.value = true;
    preferencesSavedHint.value = '';
  }

  async function savePreferences(): Promise<void> {
    saveCreatorPreferencesLocal(preferences.value);
    try {
      // v16.2.7 T8: typed wrapper's CreatorPreferencesSaveRequest is strict;
      // legacy shape was loose. Cast preserves runtime behavior.
      await saveCreatorPreferences(preferencesToApi(preferences.value) as unknown as Parameters<typeof saveCreatorPreferences>[0]);
      preferencesSyncSource.value = 'server';
      preferencesSavedHint.value = '偏好已同步到项目';
      saveMessage.value = '创作偏好已保存';
    } catch (e) {
      preferencesSyncSource.value = 'local';
      preferencesSavedHint.value = '已保存到本机（服务器暂不可用）';
      saveMessage.value = '创作偏好已保存到本机';
      error.value = e instanceof Error ? e.message : String(e);
    }
    preferencesDirty.value = false;
  }

  return {
    preferences,
    preferencesDirty,
    preferencesSavedHint,
    preferencesSyncSource,
    creatorModelOptions,
    loadCreatorModels,
    loadPreferencesFromServer,
    markPreferencesDirty,
    resetPreferences,
    savePreferences,
  };
}
