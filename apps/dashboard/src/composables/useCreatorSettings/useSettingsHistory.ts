/**
 * useSettingsHistory — 设定历史快照加载与回滚
 *
 * Phase 19 Task 3：从 useCreatorSettings.js 拆出（完整实现）。
 * Phase 126 v16.2.2 T4b：迁到 typed wrapper `'../../api/settings.js'`。
 * `request()` 自动加 `/api/` 前缀（v16.2.1 教训）。
 *
 * 负责: settingsHistory 列表 + loadSettingsHistory + restoreSettingsHistory +
 *       formatHistoryTime helper。
 */
import { ref, shallowRef } from 'vue';
import type { Ref } from 'vue';
import {
  fetchSettingsHistory,
  restoreSettingsSnapshot,
} from '../../api/settings.js';
import type { CreatorSettingsHistoryResponse } from '@lingwen/dashboard-contracts/shared';
import { parseSettingsHistory } from '@/utils/settingsHistoryUtils';

interface SettingsSnapshot {
  id: string;
  saved_at?: string;
  created_at?: string;
  label?: string;
  pillars_excerpt?: string;
  outline_excerpt?: string;
  global_outline_excerpt?: string;
  pillars_lines?: number;
  global_outline_lines?: number;
  message?: string;
  author?: string;
}

export interface SettingsHistoryDeps {
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  handleSaveError: (err: unknown) => void;
}

export interface SettingsHistoryReturn {
  settingsHistory: Ref<SettingsSnapshot[]>;
  formatHistoryTime: (iso: string) => string;
  loadSettingsHistory: () => Promise<void>;
  restoreSettingsHistory: (snapshotId: string) => Promise<void>;
}

export function useSettingsHistory(deps: SettingsHistoryDeps): SettingsHistoryReturn {
  const { error, saveMessage, handleSaveError } = deps;

  const settingsHistory = shallowRef<SettingsSnapshot[]>([]); // Phase 78: shallowRef — wholesale replacement

  function formatHistoryTime(iso: string): string {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleString('zh-CN', { hour12: false });
    } catch {
      return iso;
    }
  }

  async function loadSettingsHistory(): Promise<void> {
    try {
      const data: CreatorSettingsHistoryResponse = await fetchSettingsHistory();
      // Phase 126 v16.5 #N.13 T4.P3.f: utility handles canonical `snapshots`
      // + legacy `history` key fallback — composable no longer casts the typed DTO.
      settingsHistory.value = parseSettingsHistory(data);
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      settingsHistory.value = [];
    }
  }

  async function restoreSettingsHistory(snapshotId: string): Promise<void> {
    try {
      await restoreSettingsSnapshot({ snapshot_id: snapshotId });
      saveMessage.value = '已回滚到指定快照';
    } catch (e) {
      handleSaveError(e);
    }
  }

  return {
    settingsHistory,
    formatHistoryTime,
    loadSettingsHistory,
    restoreSettingsHistory,
  };
}
