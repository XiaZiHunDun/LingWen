/**
 * useCreatorMode — 创作者模式的「单一来源」composable（REQ-001 切片 A）
 *
 * 收敛三件事，供书桌/写栏工作台与后续切片统一取用：
 * - 当前激活模式（从 overview.creation_mode 读取，含项目感知的 effective 派生）
 * - 各矩阵面板在当前模式下的可见性 / 默认折叠判定
 * - 工作台布局开关与「人类习惯书桌」标记
 *
 * 目标：消除各消费方各自 import creatorPanelMatrix 工具函数的分叉，
 * 让「当前模式 + 可见性」只在此处解析。
 */
import { computed } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { useEffectiveCreationMode } from './useEffectiveCreationMode.js';
import {
  isWriteWorkbenchLayoutEnabled as isWbLayoutEnabled,
  isWriteWorkbenchPanelVisible as isWbPanelVisible,
  isHumanFirstDeskMode as isHfdMode,
  isPanelDefaultCollapsed as isPanDefaultCollapsed,
} from '../config/creatorPanelMatrix.js';

type UIProfile = Record<string, unknown>;
/** 任一 priority 矩阵：{ panelId: { mode: priority } } */
type ModeMatrix = Record<string, Record<string, 'required' | 'optional' | 'optional_collapsed' | 'hidden'>>;

export interface CreatorModeDeps {
  /** overview 来源；缺失时回退 companion */
  source: Ref<{ creation_mode?: string | null; slug?: string; name?: string } | null>;
  /** 项目来源（effective mode 会据此做项目级 fallback） */
  project?: Ref<{ slug?: string; name?: string } | null>;
}

export interface CreatorModeReturn {
  /** 当前生效模式（companion / advance / studio，本项目未知或非法时回退） */
  creationMode: ComputedRef<string>;
  isMode: (mode: string) => boolean;
  isWriteWorkbenchLayoutEnabled: (uiProfile: UIProfile) => boolean;
  isWriteWorkbenchPanelVisible: (panelId: string) => boolean;
  isPanelCollapsed: (matrix: ModeMatrix, panelId: string) => boolean;
  isHumanFirstDesk: () => boolean;
}

export function useCreatorMode({ source, project }: CreatorModeDeps): CreatorModeReturn {
  const creationMode = useEffectiveCreationMode(
    computed(() => source.value?.creation_mode ?? 'companion'),
    project,
  );

  function isMode(mode: string): boolean {
    return creationMode.value === mode;
  }

  function isWriteWorkbenchLayoutEnabled(uiProfile: UIProfile): boolean {
    return isWbLayoutEnabled(creationMode.value, uiProfile);
  }

  function isWriteWorkbenchPanelVisible(panelId: string): boolean {
    return isWbPanelVisible(creationMode.value, panelId);
  }

  function isPanelCollapsed(matrix: ModeMatrix, panelId: string): boolean {
    return isPanDefaultCollapsed(matrix, creationMode.value, panelId);
  }

  function isHumanFirstDesk(): boolean {
    return isHfdMode(creationMode.value);
  }

  return {
    creationMode,
    isMode,
    isWriteWorkbenchLayoutEnabled,
    isWriteWorkbenchPanelVisible,
    isPanelCollapsed,
    isHumanFirstDesk,
  };
}