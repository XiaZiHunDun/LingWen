<template>
  <div class="overview-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">追读力总览</h1>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        @click="refresh"
        :disabled="loading"
      >
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </header>

    <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
      {{ error }}
    </div>

    <section
      v-if="showOverviewEmptyGuide"
      class="overview-empty-guide pixel-card"
      data-testid="overview-empty-guide"
    >
      <p class="overview-empty-title">本书尚无追读力数据</p>
      <p v-if="isReadonlyInsight" class="overview-empty-hint" data-testid="overview-empty-reviewer-hint">
        审阅模式下无法代您发起写作或生产。请联系作者更新正文后，再回来看钩子与爽点趋势。
      </p>
      <p v-else class="overview-empty-hint">
        追读力统计来自已发布正文。可先写 ch001，或在「生产」页跑 Preflight / Batch 产章后再回来看钩子与爽点趋势。
      </p>
      <div class="overview-empty-actions" v-if="!isReadonlyInsight">
        <button type="button" class="empty-cta-btn pixel-border" data-testid="overview-go-creator-btn" @click="goCreator">
          去创作页
        </button>
        <button type="button" class="empty-cta-btn pixel-border" data-testid="overview-go-produce-btn" @click="goProduce">
          去生产
        </button>
      </div>
    </section>

    <template v-if="!showOverviewEmptyGuide">
    <section class="stats-section">
      <StatCard
        v-for="stat in statCards"
        :key="stat.label"
        :label="stat.label"
        :value="stat.value"
        :trend="stat.trend"
      />
    </section>

    <section class="chart-section">
      <HookTrendChart :data="chartData" />
    </section>

       <section class="chart-section">
      <CoolpointChart :data="chartData" />
    </section>

    <section class="table-section">
      <ChapterTable v-if="chapters.length > 0" :chapters="chapters" />
      <p v-else class="chapters-empty" data-testid="chapters-empty">暂无章节</p>
    </section>
    </template>
  </div>
</template>

<script setup>
// Phase 8.34: 拆数据源到 module-level singleton store
//   useOverviewStore (Phase 8.34 Task 3, 含 9a241f9 envelope 修正): 管 overview 概览
//   + chapters 列表 (REST 拉, Promise.all 并行) + loading + lastError, 替换
//   page-local 4 个 ref + loadData + onMounted + fetchOverview/fetchChapters import
// 页面 UI state (chartData / statCards computed) 仍 page-local, 从 store.overview /
//   store.chapters 派生 (store 已做 envelope 解包, chapters 是 bare array)
import { computed, inject } from 'vue'
import StatCard from '../components/StatCard.vue'
import HookTrendChart from '../components/HookTrendChart.vue'
import CoolpointChart from '../components/CoolpointChart.vue'
import ChapterTable from '../components/ChapterTable.vue'
import { useOverviewStore } from '../composables/useOverviewStore.js'
import { useDashboardNav } from '../composables/useDashboardNav.js'

const store = useOverviewStore()
const { navigateTo } = useDashboardNav()
const isReadonlyInsight = inject('isReadonlyInsight', computed(() => false))

// Phase 8.45.2: 模板 binding 兼容 — 恢复 Phase 8.34 漏改的 3 个 template
// binding (loading / error / chapters 引用 undefined 的 latent bug).
// refresh 走 thin pass-through wrapper 在本 commit 一并清理, 不算 latent bug.
// 解构 store fields + error alias (lastError), 跟 Phase 8.34 之前 page-local
// refs 同命名. Vue 3 在 template context 自动 unwrap top-level refs, destructured
// refs 仍 reactive.
const { loading, chapters, refresh } = store
const error = store.lastError

const showOverviewEmptyGuide = computed(() => {
  if (loading.value || error.value) return false
  if (store.chapters.value.length > 0) return false
  const o = store.overview.value || {}
  return (o.total_chapters ?? 0) === 0 && (o.total_hooks ?? 0) === 0
})

function goCreator() {
  navigateTo('creator')
}

function goProduce() {
  navigateTo('produce', { tab: 'studio' })
}

// chartData 派生 chapters (按 hook_count / coolpoint_count 投影)
const chartData = computed(() => {
  return store.chapters.value.map(ch => ({
    chapter: ch.chapter,
    hook_count: ch.hook_count,
    coolpoint_count: ch.coolpoint_count
  }))
})

// statCards 派生 overview (5 张 stat card 模板)
const statCards = computed(() => {
  const o = store.overview.value || {}
  return [
    {
      label: '总章节数',
      value: o.total_chapters ?? 0,
      trend: undefined
    },
    {
      label: '总钩子数',
      value: o.total_hooks ?? 0,
      trend: undefined
    },
    {
      label: '平均钩子强度',
      value: o.avg_hook_strength != null
        ? (o.avg_hook_strength * 100).toFixed(1) + '%'
        : '-',
      trend: undefined
    },
    {
      label: '总爽点数',
      value: o.total_coolpoints ?? 0,
      trend: undefined
    },
    {
      label: '平均爽点密度',
      value: o.avg_coolpoint_density != null
        ? (o.avg_coolpoint_density * 100).toFixed(1) + '%'
        : '-',
      trend: undefined
    }
  ]
})
</script>

<style scoped>
.overview-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: var(--text-xl);
  font-weight: bold;
  color: var(--color-text);
  font-family: var(--font-ui);
}

.refresh-btn {
  background-color: var(--bg-secondary);
  color: var(--color-text);
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  cursor: pointer;
  transition: background-color 0.1s;
}

.refresh-btn:hover:not(:disabled) {
  background-color: var(--color-accent);
  color: white;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-banner {
  background-color: var(--color-danger);
  color: white;
  padding: var(--space-md);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
}

.stats-section {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.stats-section > * {
  flex: 1;
  min-width: 120px;
}

.chart-section {
  width: 100%;
}

.table-section {
  width: 100%;
}

.overview-empty-guide {
  padding: var(--space-lg);
  text-align: center;
}

.overview-empty-title {
  font-size: var(--text-lg);
  font-family: var(--font-ui);
  margin-bottom: var(--space-sm);
}

.overview-empty-hint {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  line-height: 1.6;
  max-width: 520px;
  margin: 0 auto var(--space-md);
}

.overview-empty-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: center;
  flex-wrap: wrap;
}

.empty-cta-btn {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  cursor: pointer;
}

.empty-cta-btn:hover {
  background: var(--color-accent);
  color: white;
}

.chapters-empty {
  text-align: center;
  color: var(--color-text-dim);
  padding: var(--space-md);
}
</style>
