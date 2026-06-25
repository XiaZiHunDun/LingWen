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
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="loading"
        @click="refresh"
      >
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </header>

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
import { computed, onMounted } from 'vue';
import { useTodayHub } from '../composables/useTodayHub.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';

const { snapshot, loading, lastError, refresh } = useTodayHub();
const { navigateTo } = useDashboardNav();

onMounted(() => {
  refresh();
});

const quickLinks = computed(() => [
  { id: 'creator', label: '创作', icon: '✍️', nav: 'creator' },
  { id: 'produce', label: '生产', icon: '🏭', nav: 'produce', tab: 'studio' },
  { id: 'inbox', label: '待办', icon: '📥', nav: 'inbox', tab: 'decisions' },
  { id: 'insight', label: '洞察', icon: '📊', nav: 'insight', tab: 'overview' },
]);

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
