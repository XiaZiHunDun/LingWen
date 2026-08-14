/**
 * useSettingsHistory — 设定历史快照加载与回滚
 *
 * Phase 19 Task 3 占位：useCreatorSettings.js 711 行拆为 3 子模块之一。
 * 负责: settingsHistory 列表 + loadSettingsHistory + restoreSettingsHistory +
 *       formatHistoryTime 辅助。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface SettingsSnapshot {
  id: string;
  created_at?: string;
  author?: string;
  pillars_excerpt?: string;
  outline_excerpt?: string;
}

export interface SettingsHistoryDeps {
  // 暂未使用（待后续会话填充）
}

export interface SettingsHistoryReturn {
  settingsHistory: Ref<SettingsSnapshot[]>;
  formatHistoryTime: (iso: string) => string;
  loadSettingsHistory: () => Promise<void>;
  restoreSettingsHistory: (snapshotId: string) => Promise<void>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useSettingsHistory(_deps: SettingsHistoryDeps): SettingsHistoryReturn {
  throw new Error('useSettingsHistory: not yet implemented (Phase 19 Task 3.1)');
}