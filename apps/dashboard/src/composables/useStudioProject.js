import { useStudioStore } from '../stores/useStudioStore.js';

/**
 * Composable for managing studio project state
 * Wraps useStudioStore with bound action methods
 * @returns {ReturnType<import('../stores/useStudioStore.js').useStudioStore>}
 */
export function useStudioProject() {
  const store = useStudioStore();
  return {
    projects: store.projects,
    activeSlug: store.activeSlug,
    summary: store.summary,
    quality: store.quality,
    qualityReport: store.qualityReport,
    proseDiff: store.proseDiff,
    proseJudge: store.proseJudge,
    loading: store.loading,
    error: store.error,
    projectRevision: store.projectRevision,
    loadProjects: store.loadProjects.bind(store),
    switchProject: store.switchProject.bind(store),
    refresh: store.refresh.bind(store),
    bumpProjectRevision: store.bumpProjectRevision.bind(store),
  };
}
