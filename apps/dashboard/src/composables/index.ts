/**
 * Composables 统一导出入口（Phase 19-20 重构后）
 *
 * 主 hook（按业务领域分组）：
 *
 * - 工具: creatorDefaultUiProfile, useApiConnectivity, useAskAssistant, useCostWindow, TIME_OPTIONS
 * - 批量/批次: useCreatorAdvanceBatch, useCreatorBatchHistory
 * - 设定: useCreatorSettings
 * - 创作页编排: useCreatorPage（含 chrome 子模块 useCreatorPageChrome）
 * - 模板: useCreatorVolumePlanTemplates（含子模块 useTemplateList/Editor/Sync）
 * - 卷纲: useCreatorVolumePlan, useCreatorVolumePlanDiff（含子模块 useVolumePlanDiff/Share）
 * - 创作工具: useCreatorProductTools（含子模块 useProductPreferences/Export/Publish/Memory）
 * - 助手: useCreatorAgent（含子模块 useAgentConfig/Task/Tools）
 * - 入门: useCreatorOnboarding（含子模块 useWizardSteps/OnboardingProgress/OnboardingNotifications）
 * - 写作: useCreatorWrite（含子模块 useWriteFlow/WriteTools）
 * - 引导: useCreatorModeGuide
 * - 工作台: useCreatorWriteWorkbench, useWorkbenchIndex
 * - 页面: useCreatorPageHeader, useCreatorPageProviders, useCreatorPageRefresh
 * - 仪表盘: useCreatorPulse
 * - 工作区: useCreatorWorkspace
 * - 数据/导航: useDashboardNav, useDashboardRole, useRippleSocket, useRippleStore,
 *   useEffectiveCreationMode, useDecisionStore, useOverviewStore, usePageLeadDismiss,
 *   useTodayHub, useTierBudgetAlerts, useWorkflowListStore, useWidgetRegistry, useDashboardWidgets
 * - 事件总线: useEventBus
 * - 工作流 socket: useWorkflowSocket
 * - 业务工具: useAskPageTab, useStudioProject, useFilteredPageError, useDevice,
 *   volumePlanDiffExportUtils
 *
 * 子模块（Phase 19-20 拆分）：
 * - useCreatorProductTools/{useProductPreferences,useProductExport,useProductPublish,useProductMemory}
 * - useCreatorSettings/{useSettingsHistory,useMergePresets,useSettingsDocs}
 * - useCreatorVolumePlanTemplates/{useTemplateList,useTemplateEditor,useTemplateSync}
 * - useCreatorBatchHistory/{useBatchList,useBatchDiff,useBatchRestore}
 * - useCreatorWrite/{useWriteFlow,useWriteValidation,useWriteTools}
 * - useCreatorOnboarding/{useWizardSteps,useOnboardingProgress,useOnboardingNotifications}
 * - useCreatorAgent/{useAgentConfig,useAgentTask,useAgentTools}
 * - useCreatorVolumePlanDiff/{useVolumePlanDiff,useVolumePlanDiffShare}
 * - useCreatorPage/{useCreatorPageChrome}
 * 详见 composables.d.ts 类型声明。
 */

export { creatorDefaultUiProfile } from './creatorDefaultUiProfile.js';
export { useApiConnectivity } from './useApiConnectivity.js';
export { useAskAssistant, useAskPageTab, ASK_LONG_DRAFT_CHAR_LIMIT } from './useAskAssistant.js';
export { useCostWindow } from './useCostWindow.js';
export { TIME_OPTIONS } from './useTimeOptions.js';
export { useCreatorAdvanceBatch } from './useCreatorAdvanceBatch.js';
export { useCreatorAgent } from './useCreatorAgent.js';
export { useCreatorBatchHistory } from './useCreatorBatchHistory.js';
export { useCreatorModeGuide } from './useCreatorModeGuide.js';
export { useCreatorOnboarding } from './useCreatorOnboarding.js';
export { useCreatorPage } from './useCreatorPage.js';
export { useCreatorPageHeader } from './useCreatorPageHeader.js';
export { useCreatorPageProviders } from './useCreatorPageProviders.js';
export { createCreatorPageRefresh } from './useCreatorPageRefresh.js';
export { useCreatorProductTools } from './useCreatorProductTools.js';
export { useCreatorPulse } from './useCreatorPulse.js';
export { useCreatorSettings } from './useCreatorSettings.js';
export { useCreatorVolumePlan } from './useCreatorVolumePlan.js';
export { useCreatorVolumePlanDiff } from './useCreatorVolumePlanDiff.js';
export { useCreatorVolumePlanMergeSplit } from './useCreatorVolumePlanMergeSplit.js';
export { useCreatorVolumePlanTemplates } from './useCreatorVolumePlanTemplates.js';
export { useCreatorWorkspace } from './useCreatorWorkspace.js';
export { useCreatorWrite } from './useCreatorWrite.js';
export { useCreatorWriteWorkbench } from './useCreatorWriteWorkbench.js';
export { useDashboardNav } from './useDashboardNav.js';
export { useDashboardRole } from './useDashboardRole.js';
export { useDecisionStore } from './useDecisionStore.js';
export { useEffectiveCreationMode } from './useEffectiveCreationMode.js';
export { useFilteredPageError } from './useFilteredPageError.js';
export { useOverviewStore } from './useOverviewStore.js';
export { usePageLeadDismiss } from './usePageLeadDismiss.js';
export { useRippleSocket } from './useRippleSocket.js';
export { useRippleStore } from './useRippleStore.js';
export { useStudioProject } from './useStudioProject.js';
export { useTierBudgetAlerts } from './useTierBudgetAlerts.js';
// useTimeOptions 不导出 useTimeOptions，只有 TIME_OPTIONS
export { useTodayHub } from './useTodayHub.js';
export { useWorkflowListStore } from './useWorkflowListStore.js';
export { useWorkflowSocket, onCascadeUpdate, onAuditCreated } from './useWorkflowSocket.js';
export { useEventBus, onRippleUpdate, onWsConnected, onWsDisconnected } from './useEventBus.js';
export { useWidgetRegistry, defineWidget, registerWidget, registerWidgets, getWidget, getAllWidgets, getWidgetsByCategory, unregisterWidget, createWidgetInstance, getWidgetInstance, removeWidgetInstance, updateWidgetInstance, setWidgetInstanceState, getWidgetInstanceState, emitWidgetEvent, onWidgetEvent, checkWidgetDependencies } from './useWidgetRegistry.js';
export { useWorkbenchSelection, useWorkbenchCheckpoint, useWorkbenchValidation, useWorkbenchAgent } from './useWorkbenchIndex.js';
export { registerDashboardWidgets, getDefaultDashboardLayout } from './useDashboardWidgets.js';
export { useDevice } from './useDevice.js';
export * as volumePlanDiffExportUtils from './volumePlanDiffExportUtils.js';

// Phase 19-20 子模块聚合（提供细粒度依赖注入）
export {
  useProductPreferences,
  useProductExport,
  useProductPublish,
  useProductMemory,
} from './useCreatorProductTools/index';
export {
  useSettingsHistory,
  useMergePresets,
  useSettingsDocs,
} from './useCreatorSettings/index';
export {
  useTemplateList,
  useTemplateEditor,
  useTemplateSync,
} from './useCreatorVolumePlanTemplates/index';
export {
  useBatchList,
  useBatchDiff,
  useBatchRestore,
} from './useCreatorBatchHistory/index';
export {
  useWriteFlow,
  useWriteValidation,
  useWriteTools,
} from './useCreatorWrite/index';
export {
  useWizardSteps,
  useOnboardingProgress,
  useOnboardingNotifications,
} from './useCreatorOnboarding/index';
export {
  useAgentConfig,
  useAgentTask,
  useAgentTools,
} from './useCreatorAgent/index';
export {
  useVolumePlanDiff,
  useVolumePlanDiffShare,
} from './useCreatorVolumePlanDiff/index';
export { useCreatorPageChrome } from './useCreatorPage/index';
// Phase 60: useWorkbenchSelection aliased to avoid conflict with legacy
// useWorkbenchIndex.js re-export (Phase 19-20 placeholders, superseded by
// useCreatorWriteWorkbench/{useWorkbench*} submodules).
export {
  useWorkbenchLayout,
  useWorkbenchSelection as useCreatorWorkbenchSelection,
  useWorkbenchCheckpoints,
  useWorkbenchQuality,
} from './useCreatorWriteWorkbench/index';