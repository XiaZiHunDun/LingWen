<!--
  TodayPage.vue — 工具箱 · 今日概览
-->
<template>
  <div class="today-page l1-page" data-testid="today-page">
    <div class="today-hero">
      <img src="/assets/illustrations/hero_1280x720.jpg" alt="创作场景" class="today-hero__image">
      <div class="today-hero__overlay"></div>
      <div class="today-hero__content">
        <span class="today-hero__tag">AI创作助手</span>
        <h1 class="today-hero__title">墨灵</h1>
        <p class="today-hero__subtitle">让每个故事，都有人陪你写完</p>
      </div>
    </div>
    <div class="l1-page__body l1-panel-enter">
      <div class="l1-lead-row">
        <PageLeadBar
          page-id="today"
          inline
          text="任务、健康度与快捷入口——日常写作请回「书桌」"
        />

      </div>

      <p v-if="snapshot" class="project-line" data-testid="today-project-line">
        {{ snapshot.projectName }}
      </p>

    <div
      v-if="isReviewer"
      class="reviewer-banner"
      data-testid="today-reviewer-banner"
    >
      审阅视图：今日页仅展示待办与健康度摘要，不可发起创作或生产。
    </div>

    <div v-if="displayError" class="error-banner" data-testid="error-banner">
      {{ displayError }}
    </div>

    <section v-if="snapshot" class="primary-card" data-testid="today-primary-action">
      <p class="primary-reason">{{ snapshot.primaryAction.reason }}</p>
      <button
        type="button"
        class="l1-pill l1-pill--primary today-primary-cta"
        data-testid="today-primary-cta"
        @click="onPrimaryAction"
      >
        {{ snapshot.primaryAction.label }}
      </button>
    </section>

    <section v-if="snapshot" class="health-section" data-testid="today-health-section">
      <h2 class="section-title">本书健康度</h2>
      <div class="health-grid">
        <div class="health-stat">
          <span class="health-stat__label">正文进度</span>
          <strong class="health-stat__value">{{ snapshot.health.chaptersWritten }}/{{ snapshot.health.maxChapter }}</strong>
          <span class="health-stat__hint">{{ snapshot.health.coveragePct }}%</span>
        </div>
        <div class="health-stat">
          <span class="health-stat__label">Batch</span>
          <strong class="health-stat__value">{{ snapshot.health.batchActive ? '进行中' : '空闲' }}</strong>
        </div>
        <div class="health-stat">
          <span class="health-stat__label">质检报告</span>
          <strong class="health-stat__value">{{ snapshot.health.qualityReportReady ? '已有' : '暂无' }}</strong>
        </div>
        <div v-if="snapshot.wizardProgressPct < 100" class="health-stat">
          <span class="health-stat__label">入门向导</span>
          <strong class="health-stat__value">{{ snapshot.wizardProgressPct }}%</strong>
        </div>
        <div
          v-if="snapshot.health.microTask && !snapshot.health.microTask.met"
          class="health-stat"
          data-testid="today-micro-task-stat"
        >
          <span class="health-stat__label">本章字数</span>
          <strong class="health-stat__value">
            还差 {{ snapshot.health.microTask.remaining }}
          </strong>
          <span class="health-stat__hint">
            {{ snapshot.health.microTask.current }}/{{ snapshot.health.microTask.goal }}
          </span>
        </div>
      </div>
    </section>

    <div v-if="loading && !snapshot" class="loading-state" data-testid="today-loading">
      加载今日任务…
    </div>

    <div v-if="!loading && !snapshot" class="empty-state" data-testid="today-empty-state">
      <img src="/assets/illustrations/empty-state-no-task.jpg" alt="今日无事" class="empty-state__image" />
      <h3 class="empty-state__title">今日无事</h3>
      <p class="empty-state__desc">享受悠闲时光，灵感总会不期而至</p>
    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import { useTodayHub } from '../composables/useTodayHub.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { useFilteredPageError } from '../composables/useFilteredPageError.js';
import { copyDashboardShareUrl } from '../utils/shareLink.js';

const { snapshot, loading, lastError, refresh } = useTodayHub();
const displayError = useFilteredPageError(lastError);
const { navigateTo } = useDashboardNav();
const isReviewer = inject('isReviewer', computed(() => false));
const shareMessage = ref('');

onMounted(() => {
  reload();
});

function reload() {
  refresh({ isReviewer: isReviewer.value });
}

async function copyShareLink() {
  const tab = snapshot.value?.primaryAction?.tab === 'ripples' ? 'ripples' : 'decisions';
  const result = await copyDashboardShareUrl({
    nav: 'inbox',
    tab,
    role: 'reviewer',
  });
  shareMessage.value = result.ok ? '已复制链接' : '复制失败';
  if (result.ok) {
    setTimeout(() => { shareMessage.value = ''; }, 2000);
  }
}

function go(nav, tab) {
  navigateTo(nav, { clearFocus: true, tab });
}

function onPrimaryAction() {
  const action = snapshot.value?.primaryAction;
  if (!action) return;
  navigateTo(action.nav, {
    clearFocus: action.chapter == null,
    chapter: action.chapter,
    wizard: Boolean(action.wizard),
    tab: action.tab,
  });
}
</script>

<style scoped>
.today-page {
  flex: 1;
  min-height: 0;
}

.today-hero {
  position: relative;
  width: 100%;
  height: 220px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-lg);
  border-radius: var(--radius-lg);
}

.today-hero__image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.65;
}

.today-hero__overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(43, 35, 24, 0.3) 0%, rgba(43, 35, 24, 0.65) 100%);
}

.today-hero__content {
  position: relative;
  z-index: 2;
  text-align: center;
  color: #fffdf8;
  padding: 1rem;
}

.today-hero__tag {
  display: inline-block;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  letter-spacing: 0.15em;
  padding: 4px 14px;
  border: 1px solid rgba(255, 253, 248, 0.6);
  border-radius: 2px;
  margin-bottom: 1rem;
}

.today-hero__title {
  font-family: var(--font-heading);
  font-size: 2.2rem;
  font-weight: 400;
  line-height: 1.2;
  margin-bottom: 0.4rem;
  letter-spacing: 0.04em;
}

.today-hero__subtitle {
  font-family: var(--font-body);
  font-size: 1rem;
  font-style: italic;
  opacity: 0.9;
  max-width: 400px;
  margin: 0 auto;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
  flex-shrink: 0;
}

.reviewer-banner {
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-sm);
  background: var(--bg-muted);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--color-accent);
}

.project-line {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-dim);
}

.primary-card {
  padding: var(--space-lg);
  text-align: center;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-muted);
}

.primary-reason {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  margin-bottom: var(--space-md);
}

.today-primary-cta {
  font-size: var(--text-sm);
  padding: 10px 20px;
}

.today-secondary-links {
  margin: var(--space-md) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 2px var(--space-xs);
}

.today-secondary-links__sep {
  opacity: 0.5;
  user-select: none;
}

.today-secondary-link {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  font-size: var(--text-sm);
  color: var(--color-accent);
  text-decoration: underline;
  cursor: pointer;
}

.today-secondary-link:hover {
  opacity: 0.85;
}

.empty-state {
  text-align: center;
  padding: var(--space-xl) var(--space-lg);
}

.empty-state__image {
  max-width: 320px;
  height: auto;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  opacity: 0.9;
}

.empty-state__title {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 400;
  margin-bottom: var(--space-xs);
}

.empty-state__desc {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  margin-bottom: var(--space-md);
}

.section-title {
  font-size: var(--text-lg);
  font-family: var(--font-ui);
  font-weight: 600;
  margin: 0 0 var(--space-sm);
  color: var(--color-text);
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--space-sm);
}

.health-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.health-stat__label {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.health-stat__value {
  font-size: var(--text-md);
}

.health-stat__hint {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.health-section {
  padding: var(--space-md);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-muted);
}

.error-banner {
  background: var(--color-danger);
  color: white;
  padding: var(--space-md);
  font-size: var(--text-sm);
}

.loading-state {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-dim);
  font-size: var(--text-sm);
}
</style>
