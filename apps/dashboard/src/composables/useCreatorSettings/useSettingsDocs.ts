/**
 * useSettingsDocs — 设定文档编辑 + 3-way diff + 保存流程
 *
 * Phase 19 Task 3 占位：useCreatorSettings.js 711 行拆为 3 子模块之一。
 * 负责: settingsDocs 加载 + diff 预览 + mergeStrategy preview + requestSaveSettings +
 *       confirmSaveSettings + bindGlobalOutlineEditorRef。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface SettingsDocs {
  pillars?: string;
  outline?: string;
}

export interface SettingsDocsDeps {
  // 暂未使用（待后续会话填充）
}

export interface SettingsDocsReturn {
  settingsDocs: Ref<SettingsDocs | null>;
  pillarsText: Ref<string>;
  settingsBaseline: Ref<{ pillars: string; outline: string }>;
  settingsDiffPreview: Ref<unknown>;
  showSettingsDiff: Ref<boolean>;
  settingsSaving: Ref<boolean>;
  mergeStrategyPreview: Ref<unknown>;
  threeWayPreview: Ref<unknown>;
  loadSettingsDocs: () => Promise<void>;
  refreshMergeStrategyPreview: () => Promise<void>;
  refreshThreeWayPreview: () => Promise<void>;
  requestSaveSettings: () => Promise<void>;
  confirmSaveSettings: () => Promise<void>;
  cancelSettingsDiff: () => void;
  bindGlobalOutlineEditorRef: (el: HTMLElement | null) => void;
}

// 占位实现 — 后续会话填充实际逻辑
export function useSettingsDocs(_deps: SettingsDocsDeps): SettingsDocsReturn {
  throw new Error('useSettingsDocs: not yet implemented (Phase 19 Task 3.3)');
}