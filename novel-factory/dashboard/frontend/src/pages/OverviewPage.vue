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
      <ChapterTable :chapters="chapters" />
    </section>
  </div>
</template>

<script setup>
// Phase 8.34: 拆数据源到 module-level singleton store
//   useOverviewStore (Phase 8.34 Task 3, 含 9a241f9 envelope 修正): 管 overview 概览
//   + chapters 列表 (REST 拉, Promise.all 并行) + loading + lastError, 替换
//   page-local 4 个 ref + loadData + onMounted + fetchOverview/fetchChapters import
// 页面 UI state (chartData / statCards computed) 仍 page-local, 从 store.overview /
//   store.chapters 派生 (store 已做 envelope 解包, chapters 是 bare array)
import { computed } from 'vue'
import StatCard from '../components/StatCard.vue'
import HookTrendChart from '../components/HookTrendChart.vue'
import CoolpointChart from '../components/CoolpointChart.vue'
import ChapterTable from '../components/ChapterTable.vue'
import { useOverviewStore } from '../composables/useOverviewStore.js'

const store = useOverviewStore()

// 模板 binding 通过 store 字段直接访问 (Vue 在 template context 自动 unwrap refs)
// store.loading / store.lastError / store.chapters 均由 store 提供, 跟 page-local
// 命名一致, template 一行不改也能 work

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

// refresh thin wrapper 委托给 store (template binding 名 refresh 保留, 跟
// WorkflowsPage 同模式, 保模板 @click="refresh" 像素级不动)
function refresh() {
  return store.refresh()
}
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
  font-size: 12px;
  font-weight: bold;
  color: var(--color-text);
  font-family: 'Press Start 2P', monospace;
}

.refresh-btn {
  background-color: var(--bg-secondary);
  color: var(--color-text);
  padding: var(--space-sm) var(--space-md);
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
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
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
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
</style>
