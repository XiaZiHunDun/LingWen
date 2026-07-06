<!--
  TodayPage.vue — 工具箱 · 今日概览
-->
<template>
  <div class="today-page l1-page" data-testid="today-page">
    <div class="l1-page__body l1-panel-enter">
      <div class="l1-lead-row">
        <PageLeadBar
          page-id="today"
          inline
          text="任务、健康度与快捷入口——日常写作请回「书桌」"
        />
        <div class="header-actions">
          <button
            v-if="isReviewer"
            type="button"
            class="l1-pill"
            :class="{ 'l1-pill--primary': shareMessage === '已复制链接' }"
            data-testid="today-share-link-btn"
            @click="copyShareLink"
          >
            {{ shareMessage || '复制审阅链接' }}
          </button>
          <button
            type="button"
            class="l1-pill"
            data-testid="refresh-btn"
            :disabled="loading"
            @click="reload"
          >
            {{ loading ? '加载中…' : '刷新' }}
          </button>
        </div>
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
      <p
        v-if="snapshot.secondaryLinks.length"
        class="today-secondary-links"
        data-testid="today-secondary-links"
      >
        <template v-for="(link, index) in snapshot.secondaryLinks" :key="link.id">
          <span v-if="index > 0" class="today-secondary-links__sep" aria-hidden="true">·</span>
          <button
            type="button"
            class="today-secondary-link"
            :data-testid="`today-secondary-${link.id}`"
            @click="go(link.nav, link.tab)"
          >
            {{ link.label }} →
          </button>
        </template>
      </p>
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
      </div>
    </section>

    <div v-if="loading && !snapshot" class="loading-state" data-testid="today-loading">
      加载今日任务…
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
    clearFocus: true,
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
