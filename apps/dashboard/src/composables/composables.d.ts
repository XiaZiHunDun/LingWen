/**
 * Phase 19-43 拆分子模块类型导出声明
 *
 * 为 Phase 19-20 拆分后新增的 .ts 子模块提供显式 .d.ts 导出，
 * 提升 IDE 自动完成和类型推导体验。
 *
 * 主 hook 仍通过 composables/index.js 暴露（向后兼容），
 * 本文件仅添加子模块级别的细粒度类型导出。
 */
declare module './useCreatorProductTools/index.js' {
  export {
    useProductPreferences,
    useProductExport,
    useProductPublish,
    useProductMemory,
  } from './useCreatorProductTools/index';
}

declare module './useCreatorSettings/index.js' {
  export {
    useSettingsHistory,
    useMergePresets,
    useSettingsDocs,
  } from './useCreatorSettings/index';
}

declare module './useCreatorVolumePlanTemplates/index.js' {
  export {
    useTemplateList,
    useTemplateEditor,
    useTemplateSync,
  } from './useCreatorVolumePlanTemplates/index';
}

declare module './useCreatorBatchHistory/index.js' {
  export {
    useBatchList,
    useBatchDiff,
    useBatchRestore,
  } from './useCreatorBatchHistory/index';
}

declare module './useCreatorWrite/index.js' {
  export {
    useWriteFlow,
    useWriteValidation,
    useWriteTools,
  } from './useCreatorWrite/index';
}

declare module './useCreatorOnboarding/index.js' {
  export {
    useWizardSteps,
    useOnboardingProgress,
    useOnboardingNotifications,
  } from './useCreatorOnboarding/index';
}

declare module './useCreatorAgent/index.js' {
  export {
    useAgentConfig,
    useAgentTask,
    useAgentTools,
  } from './useCreatorAgent/index';
}

declare module './useCreatorVolumePlanDiff/index.js' {
  export {
    useVolumePlanDiff,
    useVolumePlanDiffShare,
  } from './useCreatorVolumePlanDiff/index';
}

declare module './useCreatorPage/index.js' {
  export { useCreatorPageChrome } from './useCreatorPage/index';
}
