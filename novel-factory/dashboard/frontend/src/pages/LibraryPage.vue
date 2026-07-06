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
        <article
          v-for="p in projects"
          :key="p.slug"
          class="library-card"
          :class="{ 'library-card--active': p.slug === activeSlug }"
          :data-testid="`library-card-${p.slug}`"
          role="button"
          tabindex="0"
          @click="openBook(p.slug)"
          @keydown.enter="openBook(p.slug)"
        >
          <div class="library-card__cover">
            {{ (p.name || p.slug || '?').slice(0, 1) }}
          </div>
          <div class="library-card__body">
            <h2 class="library-card__title">{{ displayProjectName(p) }}</h2>
            <p class="meta-line">{{ projectSubtitle(p) }}</p>
            <p v-if="p.slug === activeSlug && qualityLine" class="library-card__stats">{{ qualityLine }}</p>
            <span v-if="p.slug === activeSlug" class="library-card__badge">当前</span>
          </div>
        </article>
      </div>

      <div
        v-else
        class="library-page__empty"
        data-testid="library-empty"
      >
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
  const labels = { projects: '书库', root: '仓库' };
  return labels[project?.location] || '本地';
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
  background: var(--bg-elevated);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}
.library-page__empty-title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: 600;
}
.library-page__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-md);
}
.library-card {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: var(--space-sm);
  padding: var(--space-md);
  position: relative;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
  cursor: pointer;
  text-align: left;
}
.library-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}
.library-card--active {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}
.library-card__cover {
  width: 56px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(145deg, var(--color-accent), var(--color-accent-gradient-end));
}
.library-card__title {
  margin: 0;
  font-size: var(--text-md);
}
.library-card__stats {
  margin: 4px 0 0;
  font-size: var(--text-xs);
}
.library-card__badge {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 10px;
  padding: 3px 8px;
  background: var(--color-accent);
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
}
.meta-line {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
.error-line {
  color: #c33;
  font-size: var(--text-sm);
}
</style>
