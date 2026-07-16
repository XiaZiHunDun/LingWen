<!--
  LibraryPage.vue — L1 书架（frontend-ia-v1）
-->
<template>
  <div class="library-page l1-page" data-testid="library-page">
    <p v-if="loading" class="meta-line">加载中…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else class="library-page__body l1-page__body l1-panel-enter">
      <div class="l1-lead-row">
        <PageLeadBar
          page-id="library"
          inline
          text="换书、看进度，一键回到书桌"
        />
        <button
          type="button"
          class="l1-pill l1-pill--primary"
          data-testid="library-new-btn"
          @click="startNew"
        >
          新建
        </button>
      </div>
      <div v-if="projects.length" class="library-page__grid" data-testid="library-grid">
        <button
          v-for="p in projects"
          :key="p.slug"
          type="button"
          class="library-card"
          :class="{ 'library-card--active': p.slug === activeSlug }"
          :data-testid="`library-card-${p.slug}`"
          :aria-current="p.slug === activeSlug ? 'true' : undefined"
          @click="openBook(p.slug)"
        >
          <span class="library-card__cover" aria-hidden="true">
            {{ (p.name || p.slug || '?').slice(0, 1) }}
          </span>
          <span class="library-card__body">
            <span class="library-card__title">{{ displayProjectName(p) }}</span>
            <span class="library-card__subtitle meta-line">{{ projectSubtitle(p) }}</span>
            <span v-if="p.slug === activeSlug && qualityLine" class="library-card__stats">{{ qualityLine }}</span>
            <span v-if="p.slug === activeSlug" class="library-card__badge">当前</span>
          </span>
        </button>
      </div>

      <div
        v-else
        class="library-page__empty"
        data-testid="library-empty"
      >
        <img src="/assets/illustrations/empty-state-no-project.jpg" alt="书架为空" class="library-page__empty-image" />
        <p class="library-page__empty-title">书架还是空的</p>
        <p class="meta-line">点「新建」开第一本，或在「聊聊」里说说你想写什么。</p>
        <button type="button" class="l1-pill l1-pill--primary" data-testid="library-empty-new-btn" @click="startNew">
          新建第一本书
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import { useStudioProject } from '../composables/useStudioProject.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { getWriteResume } from '../utils/writeResumeStorage.js';
import { fetchStudioQuality } from '../api/index.js';
import { formatDisplayProjectName } from '../utils/displayProjectName.js';

const studio = useStudioProject();
const { navigateTo, setWizardDeepLink } = useDashboardNav();

const loading = ref(false);
const error = ref(null);
const qualityLine = ref('');

const projects = computed(() => studio.projects.value || []);
const activeSlug = computed(() => studio.activeSlug.value);

function projectSubtitle(project) {
  const written = project?.chapter_count ?? project?.chapters_written;
  if (written != null && Number(written) > 0) return `已写 ${written} 章`;
  if (project?.has_body || project?.has_outline) return '进行中';
  return '尚未开写';
}

function displayProjectName(project) {
  return formatDisplayProjectName(project?.name || project?.slug) || project?.slug || '未命名';
}

async function openBook(slug) {
  if (slug !== activeSlug.value) {
    await studio.switchProject(slug);
  }
  const resume = getWriteResume(slug);
  navigateTo('write', { chapter: resume?.chapter ?? null, clearFocus: false });
}

/** @deprecated use openBook — kept for tests that import continueBook */
async function continueBook(slug) {
  await openBook(slug);
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    await studio.loadProjects();
    if (studio.activeSlug.value) {
      const q = await fetchStudioQuality().catch(() => null);
      if (q) {
        qualityLine.value = `已写 ${q.chapters_written ?? 0} 章 · 覆盖 ${q.coverage_pct ?? 0}%`;
      }
    }
  } catch (e) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function switchOnly(slug) {
  await studio.switchProject(slug);
  await load();
}

function startNew() {
  setWizardDeepLink(true, 'welcome', [], {});
  navigateTo('write', { wizard: true, clearFocus: true });
}

onMounted(load);
</script>

<style scoped>
.library-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: none;
  margin: 0;
}
.library-page__body {
  /* 见 style.css .l1-page__body */
}
.library-page__empty {
  padding: var(--space-xl);
  text-align: center;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-secondary) 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}
.library-page__empty-image {
  max-width: 280px;
  height: auto;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  opacity: 0.9;
  transition: transform var(--transition-slow);
}
.library-page__empty-image:hover {
  transform: scale(1.02);
}
.library-page__empty-title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: 600;
  font-family: var(--font-heading);
}
.library-page__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-md);
}
@media (min-width: 1280px) {
  .library-page__grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}
.library-card {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: var(--space-md);
  padding: var(--space-md);
  position: relative;
  width: 100%;
  font: inherit;
  color: inherit;
  background: var(--surface-elevated, var(--bg-elevated));
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  cursor: pointer;
  text-align: left;
  overflow: hidden;
}
.library-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: transparent;
  transition: background var(--transition-normal);
}
.library-card:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
@media (prefers-reduced-motion: reduce) {
  .library-card {
    transition: none;
  }
}
.library-card:hover {
  border-color: var(--color-accent);
  box-shadow: var(--shadow-elegant);
  transform: translateY(-2px);
}
.library-card:hover::before {
  background: linear-gradient(90deg, var(--color-accent), var(--color-accent3), var(--color-accent2));
}
.library-card--active {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-soft), var(--shadow-card);
}
.library-card--active::before {
  background: linear-gradient(90deg, var(--color-accent), var(--color-accent3), var(--color-accent2));
}
.library-card__cover {
  width: 64px;
  height: 80px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-accent, #fff);
  border: none;
  border-radius: var(--radius-md);
  transition: transform var(--transition-normal);
}
.library-card:hover .library-card__cover {
  transform: scale(1.05);
}
.library-card__body {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  min-width: 0;
}
.library-card__title {
  display: block;
  margin: 0;
  font-size: var(--text-md);
  font-weight: 600;
  line-height: 1.35;
  color: var(--color-text);
}
.library-card__subtitle {
  display: block;
}
.library-card__stats {
  margin: 6px 0 0;
  font-size: var(--text-xs);
  padding: 4px 10px;
  background: var(--bg-muted);
  border-radius: 12px;
}
.library-card__badge {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 10px;
  padding: 4px 10px;
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-gradient-end) 100%);
  color: var(--color-on-accent, #fff);
  border-radius: 999px;
  font-weight: 600;
}
.meta-line {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}
.error-line {
  color: var(--color-danger);
  font-size: var(--text-sm);
}

.library-card:nth-child(5n+1) .library-card__cover {
  background: linear-gradient(145deg, #7c3aed, #5b21b6);
}
.library-card:nth-child(5n+2) .library-card__cover {
  background: linear-gradient(145deg, #ec4899, #be185d);
}
.library-card:nth-child(5n+3) .library-card__cover {
  background: linear-gradient(145deg, #f59e0b, #d97706);
}
.library-card:nth-child(5n+4) .library-card__cover {
  background: linear-gradient(145deg, #06b6d4, #0891b2);
}
.library-card:nth-child(5n+5) .library-card__cover {
  background: linear-gradient(145deg, #10b981, #059669);
}
</style>
