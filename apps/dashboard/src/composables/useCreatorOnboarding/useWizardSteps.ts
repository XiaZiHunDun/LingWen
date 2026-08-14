/**
 * useWizardSteps — 向导步骤 + 分享/链接 + note/复选
 *
 * Phase 19 Task 7 占位：useCreatorOnboarding.js 555 行拆为 3 子模块之一。
 * 负责: wizardSteps 列表 + loadOnboardingWizard + toggleWizardStep +
 *       saveWizardStepNote + onWizardToggle + syncWizardPanelOpen +
 *       copyWizardShareLink + applyWizardShareFromUrl + focusWizardStepFromUrl +
 *       extractMentionsFromText。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface WizardStep {
  id: string;
  title?: string;
  description?: string;
  done?: boolean;
  linked_mode?: string;
  note?: string;
}

export interface WizardStepsDeps {
  // 暂未使用（待后续会话填充）
}

export interface WizardStepsReturn {
  wizardSteps: Ref<WizardStep[]>;
  wizardPanelOpen: Ref<boolean>;
  wizardShareLink: Ref<string>;
  loadOnboardingWizard: () => Promise<void>;
  toggleWizardStep: (stepId: string, checked: boolean) => Promise<void>;
  saveWizardStepNote: (stepId: string) => Promise<void>;
  onWizardToggle: (event: Event) => Promise<void>;
  syncWizardPanelOpen: () => void;
  copyWizardShareLink: () => Promise<void>;
  applyWizardShareFromUrl: () => Promise<void>;
  focusWizardStepFromUrl: () => Promise<void>;
  extractMentionsFromText: (text: string) => string[];
}

// 占位实现 — 后续会话填充实际逻辑
export function useWizardSteps(_deps: WizardStepsDeps): WizardStepsReturn {
  throw new Error('useWizardSteps: not yet implemented (Phase 19 Task 7.1)');
}