import { useStudioStore } from '../stores/useStudioStore.js';

/**
 * @typedef {Object} StudioProjectApi
 * @property {Array<{slug: string; name?: string}>} projects
 * @property {string|null} activeSlug - 当前活跃项目 slug
 * @property {Object|null} summary
 * @property {Object|null} quality
 * @property {Object|null} qualityReport
 * @property {Object|null} proseDiff
 * @property {Object|null} proseJudge
 * @property {boolean} loading
 * @property {string|null} error
 * @property {number} projectRevision
 * @property {(slug: string) => Promise<*>} switchProject
 * @property {(force?: boolean) => Promise<void>} refresh
 * @property {() => Promise<*>} loadProjects
 * @property {() => void} bumpProjectRevision
 */

/**
 * Composable for managing studio project state
 * Wraps useStudioStore with bound action methods
 * @returns {StudioProjectApi}
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
