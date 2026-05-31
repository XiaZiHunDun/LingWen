<template>
  <div class="overview-page">
    <header class="page-header">
      <h1 class="page-title">追读力总览</h1>
      <button
        class="refresh-btn pixel-border"
        @click="refresh"
        :disabled="loading"
      >
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </header>

    <div v-if="error" class="error-banner pixel-border">
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
      <CoolpointChart
        :data="chartData"
        :typeDistribution="typeDistribution"
      />
    </section>

    <section class="table-section">
      <ChapterTable :chapters="chapters" />
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import StatCard from '../components/StatCard.vue'
import HookTrendChart from '../components/HookTrendChart.vue'
import CoolpointChart from '../components/CoolpointChart.vue'
import ChapterTable from '../components/ChapterTable.vue'
import { fetchOverview, fetchChapters } from '../api/index.js'

const loading = ref(false)
const error = ref(null)
const overview = ref(null)
const chapters = ref([])

const chartData = computed(() => {
  return chapters.value.map(ch => ({
    chapter: ch.chapter,
    hook_count: ch.hook_count,
    coolpoint_count: ch.coolpoint_count
  }))
})

const typeDistribution = computed(() => {
  if (!overview.value || !overview.value.type_distribution) {
    return {}
  }
  return overview.value.type_distribution
})

const statCards = computed(() => {
  const o = overview.value || {}
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

const loadData = async () => {
  loading.value = true
  error.value = null

  try {
    const [overviewData, chaptersData] = await Promise.all([
      fetchOverview(),
      fetchChapters('1-30')
    ])

    overview.value = overviewData
    chapters.value = chaptersData.chapters || []
  } catch (err) {
    error.value = err.message || '加载数据失败'
  } finally {
    loading.value = false
  }
}

const refresh = () => {
  loadData()
}

onMounted(() => {
  loadData()
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