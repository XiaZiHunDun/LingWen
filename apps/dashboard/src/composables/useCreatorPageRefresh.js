/**
 * useCreatorPageRefresh — 创作页 refresh 编排（从 useCreatorPage 抽出）
 */

/**
 * @param {{
 *   overview: import('vue').Ref<object|null>,
 *   loading: import('vue').Ref<boolean>,
 *   error: import('vue').Ref<string|null>,
 *   conflictMessage: import('vue').Ref<string>,
 *   fetchOverview: () => Promise<object>,
 *   loaders: {
 *     loadVolumePlan: () => Promise<void>,
 *     loadSettingsDocs: () => Promise<void>,
 *     loadSettingsHistory: () => Promise<void>,
 *     loadVolumeTemplates: () => Promise<void>,
 *     loadTemplateSyncSources: () => Promise<void>,
 *     loadOnboardingWizard: () => Promise<void>,
 *     pollBatchJob: () => Promise<void>,
 *   },
 *   afterOverview: (ov: object) => Promise<void>,
 * }} deps
 */
export function createCreatorPageRefresh(deps) {
  const {
    overview,
    loading,
    error,
    conflictMessage,
    fetchOverview,
    loaders,
    afterOverview,
  } = deps;

  return async function refresh() {
    loading.value = true;
    error.value = null;
    conflictMessage.value = '';
    try {
      const [ov] = await Promise.all([
        fetchOverview(),
        loaders.loadVolumePlan(),
        loaders.loadSettingsDocs(),
        loaders.loadSettingsHistory(),
        loaders.loadVolumeTemplates(),
        loaders.loadTemplateSyncSources(),
        loaders.loadOnboardingWizard(),
        loaders.pollBatchJob(),
      ]);
      overview.value = ov;
      await afterOverview(ov);
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  };
}
