<!--
  TodayPage.vue — Phase A 产品壳：任务导向首页
-->
<template>
  <div class="today-page" data-testid="today-page">
    <header class="page-header">
      <div>
        <h1 class="page-title" data-testid="page-title">今日</h1>
        <p v-if="snapshot" class="project-line" data-testid="today-project-line">
          {{ snapshot.projectName }}
        </p>
      </div>
      <div class="header-actions">
        <button
          v-if="isReviewer"
          type="button"
          class="share-link-btn pixel-border"
          :class="{ 'share-link-btn--ok': shareMessage === '已复制链接' }"
          data-testid="today-share-link-btn"
          @click="copyShareLink"
        >
          {{ shareMessage || '复制审阅链接' }}
        </button>
        <button
          class="refresh-btn pixel-border"
          data-testid="refresh-btn"
          :disabled="loading"
          @click="reload"
        >
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div
      v-if="isReviewer"
      class="reviewer-banner pixel-border"
      data-testid="today-reviewer-banner"
    >
      审阅视图：今日页仅展示待办与健康度摘要，不可发起创作或生产。
    </div>

    <div v-if="lastError" class="error-banner pixel-border" data-testid="error-banner">
      {{ lastError }}
    </div>

    <section v-if="snapshot" class="primary-card pixel-card" data-testid="today-primary-action">
      <p class="primary-reason">{{ snapshot.primaryAction.reason }}</p>
      <button
        type="button"
        class="primary-cta pixel-border"
        data-testid="today-primary-cta"
        @click="onPrimaryAction"
      >
        {{ snapshot.primaryAction.label }}
      </button>
    </section>

    <section v-if="snapshot" class="todo-section" data-testid="today-todo-section">
      <h2 class="section-title">待办一览</h2>
      <div class="todo-grid">
        <button
          v-for="card in snapshot.todoCards"
          :key="card.id"
          type="button"
          class="todo-card pixel-card"
          :data-testid="`today-todo-${card.id}`"
          @click="go(card.nav, card.tab)"
        >
          <span class="todo-value">{{ card.value }}</span>
          <span class="todo-label">{{ card.label }}</span>
          <span class="todo-hint">{{ card.hint }}</span>
        </button>
      </div>
    </section>

    <section v-if="snapshot" class="health-section pixel-card" data-testid="today-health-section">
      <h2 class="section-title">本书健康度</h2>
      <ul class="health-list">
        <li>
          正文进度：<strong>{{ snapshot.health.chaptersWritten }}</strong> / {{ snapshot.health.maxChapter }} 章
          （{{ snapshot.health.coveragePct }}%）
        </li>
        <li>
          Batch 状态：
          <strong>{{ snapshot.health.batchActive ? '进行中' : '空闲' }}</strong>
        </li>
        <li>
          质检报告：
          <strong>{{ snapshot.health.qualityReportReady ? '已有' : '暂无' }}</strong>
        </li>
        <li v-if="snapshot.wizardProgressPct < 100">
          入门向导：<strong>{{ snapshot.wizardProgressPct }}%</strong>
        </li>
      </ul>
    </section>

    <section v-if="snapshot" class="quick-section" data-testid="today-quick-links">
      <h2 class="section-title">快捷入口</h2>
      <div class="quick-grid">
        <button
          v-for="link in quickLinks"
          :key="link.id"
          type="button"
          class="quick-link pixel-border"
          :data-testid="`today-quick-${link.id}`"
          @click="go(link.nav, link.tab)"
        >
          {{ link.icon }} {{ link.label }}
        </button>
      </div>
    </section>

    <div v-if="loading && !snapshot" class="loading-state" data-testid="today-loading">
      加载今日任务…
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue';
import { useTodayHub } from '../composables/useTodayHub.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { copyDashboardShareUrl } from '../utils/shareLink.js';

const { snapshot, loading, lastError, refresh } = useTodayHub();
const { navigateTo } = useDashboardNav();
const isReviewer = inject('isReviewer', computed(() => false));
const shareMessage = ref('');

onMounted(() => {
  reload();
});

function reload() {
  refresh({ isReviewer: isReviewer.value });
}

const quickLinks = computed(() => {
  const all = [
    { id: 'creator', label: '创作', icon: '✍️', nav: 'creator' },
    { id: 'produce', label: '生产', icon: '🏭', nav: 'produce', tab: 'studio' },
    { id: 'inbox', label: '待办', icon: '📥', nav: 'inbox', tab: 'decisions' },
    { id: 'insight', label: '洞察', icon: '📊', nav: 'insight', tab: 'overview' },
  ];
  if (!isReviewer.value) return all;
  return all.filter((l) => l.id === 'inbox' || l.id === 'insight');
});

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
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
}

.share-link-btn {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: 8px 12px;
  background: var(--bg-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s ease;
}

.share-link-btn--ok {
  background: var(--color-success);
  color: white;
}

.reviewer-banner {
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-sm);
  background: var(--bg-primary);
  border-left: 4px solid var(--color-accent);
}

.page-title {
  font-size: var(--text-xl);
  font-family: var(--font-ui);
  font-weight: 700;
}

.project-line {
  margin-top: var(--space-xs);
  font-size: var(--text-sm);
  color: var(--color-text-dim);
}

.refresh-btn {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  cursor: pointer;
}

.primary-card {
  padding: var(--space-lg);
  text-align: center;
}

.primary-reason {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  margin-bottom: var(--space-md);
}

.primary-cta {
  font-size: var(--text-md);
  font-family: var(--font-ui);
  font-weight: 600;
  padding: 12px var(--space-lg);
  background: var(--color-accent);
  color: white;
  cursor: pointer;
  border: 3px solid var(--border-color);
}

.section-title {
  font-size: var(--text-lg);
  font-family: var(--font-ui);
  font-weight: 600;
  margin: 0 0 var(--space-sm);
  color: var(--color-accent);
}

.todo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--space-sm);
}

.todo-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  text-align: left;
  cursor: pointer;
  border: none;
  background: var(--bg-secondary);
  transition: outline-color 0.15s ease, transform 0.1s ease;
}

.todo-card:hover {
  outline: 2px solid var(--color-accent);
  transform: translateY(-2px);
}

.todo-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  font-family: var(--font-ui);
}

.todo-label {
  font-size: var(--text-sm);
  font-weight: 600;
}

.todo-hint {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.health-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.8;
}

.quick-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.quick-link {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: 10px 14px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: background-color 0.15s ease, transform 0.1s ease;
}

.quick-link:hover {
  background: var(--bg-primary);
  transform: translateY(-1px);
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
