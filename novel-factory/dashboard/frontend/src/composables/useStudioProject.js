/**
 * Phase 10.04: Studio multi-project state (active slug + summary).
 */
import { ref } from 'vue';
import {
  fetchStudioProjects,
  fetchStudioActive,
  setStudioActive,
  fetchStudioSummary,
  fetchStudioQuality,
  fetchStudioQualityReport,
  fetchStudioProseDiff,
} from '../api/index.js';

const projects = ref([]);
const activeSlug = ref(null);
const summary = ref(null);
const quality = ref(null);
const qualityReport = ref(null);
const proseDiff = ref(null);
const loading = ref(false);
const error = ref(null);
/** Increments on project switch or batch completion — pages reload production data. */
const projectRevision = ref(0);

function bumpProjectRevision() {
  projectRevision.value += 1;
}

async function loadProjects() {
  const data = await fetchStudioProjects();
  projects.value = data.projects || [];
  activeSlug.value = data.active_slug || null;
  return data;
}

async function switchProject(slug) {
  const data = await setStudioActive(slug);
  activeSlug.value = data.slug;
  bumpProjectRevision();
  await refresh();
  return data;
}

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    await loadProjects();
    const [sum, qual, report, diff] = await Promise.all([
      fetchStudioSummary(),
      fetchStudioQuality(),
      fetchStudioQualityReport(),
      fetchStudioProseDiff(),
    ]);
    summary.value = sum;
    quality.value = qual;
    qualityReport.value = report;
    proseDiff.value = diff;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

export function useStudioProject() {
  return {
    projects,
    activeSlug,
    summary,
    quality,
    qualityReport,
    proseDiff,
    loading,
    error,
    projectRevision,
    loadProjects,
    switchProject,
    refresh,
    bumpProjectRevision,
  };
}
