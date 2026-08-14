/**
 * useSettingsHistory — 设定历史快照加载与回滚
 *
 * Phase 19 Task 3：从 useCreatorSettings.js 拆出（完整实现）。
 * 负责: settingsHistory 列表 + loadSettingsHistory + restoreSettingsHistory +
 *       formatHistoryTime helper。
 */
import { ref } from 'vue';
import type { Ref } from 'vue';
import {
  fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot,
} from '../../api/index.js';

export interface SettingsSnapshot {
  id: string;
  created_at?: string;
  author?: string;
  pillars_excerpt?: string;
  outline_excerpt?: string;
  message?: string;
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

  const settingsHistory = ref<SettingsSnapshot[]>([]);

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
      const data = await fetchCreatorSettingsHistory() as { snapshots?: SettingsSnapshot[]; history?: SettingsSnapshot[] };
      settingsHistory.value = data.snapshots || data.history || [];
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      settingsHistory.value = [];
    }
  }

  async function restoreSettingsHistory(snapshotId: string): Promise<void> {
    try {
      await restoreCreatorSettingsSnapshot(snapshotId);
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