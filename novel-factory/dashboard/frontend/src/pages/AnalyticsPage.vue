<!--
  AnalyticsPage.vue — Phase 9.77 F67: 数据分析 MVP
  - 追读力 charts (reuse Overview store + HookTrendChart / CoolpointChart)
  - 生产 KPI (WS workflow status + production_summary)
  - 涟漪统计 (useRippleStore stats)
-->
<template>
  <div class="analytics-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">数据分析</h1>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="refreshing"
        @click="refreshAll"
      >
        {{ refreshing ? '加载中…' : '刷新' }}
      </button>
    </header>

    <div v-if="errorMessage" class="error-banner pixel-border" data-testid="error-banner">
      {{ errorMessage }}
    </div>

    <section class="kpi-section" data-testid="production-kpi">
      <h2 class="section-title">正文生产 KPI</h2>
      <div class="stats-row">
        <StatCard
          v-for="card in productionKpiCards"
          :key="card.label"
          :label="card.label"
          :value="card.value"
        />
      </div>
      <ul
        v-if="productionLines.length"
        class="production-summary"
        data-testid="analytics-production-summary"
      >
        <li v-for="(line, idx) in productionLines" :key="idx">{{ line }}</li>
      </ul>
    </section>

    <section class="kpi-section" data-testid="ripple-kpi">
      <h2 class="section-title">涟漪 KPI</h2>
      <div class="stats-row">
        <StatCard
          v-for="card in rippleKpiCards"
          :key="card.label"
          :label="card.label"
          :value="card.value"
        />
      </div>
    </section>

    <section class="chart-section">
      <h2 class="section-title">追读力趋势</h2>
      <HookTrendChart :data="chartData" />
    </section>

    <section class="chart-section">
      <CoolpointChart :data="chartData" />
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import StatCard from '../components/StatCard.vue';
import HookTrendChart from '../components/HookTrendChart.vue';
import CoolpointChart from '../components/CoolpointChart.vue';
import { useOverviewStore } from '../composables/useOverviewStore.js';
import { useRippleStore } from '../composables/useRippleStore.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';
import {
  buildProductionKpiCards,
  buildRippleKpiCards,
} from '../utils/analyticsKpi.js';
import {
  productionSummaryLines,
  resolveProductionSummary,
} from '../utils/productionSummary.js';

const overviewStore = useOverviewStore();
const rippleStore = useRippleStore();
const { status } = useWorkflowSocket();

const refreshing = ref(false);

const errorMessage = computed(() =>
  overviewStore.lastError.value || rippleStore.lastError.value || null,
);

const chartData = computed(() =>
  overviewStore.chapters.value.map((ch) => ({
    chapter: ch.chapter,
    hook_count: ch.hook_count,
    coolpoint_count: ch.coolpoint_count,
  })),
);

const productionKpiCards = computed(() => buildProductionKpiCards(status.value));
const rippleKpiCards = computed(() => buildRippleKpiCards(rippleStore.stats.value));
const productionLines = computed(() =>
  productionSummaryLines(resolveProductionSummary(status.value)),
);

async function refreshAll() {
  refreshing.value = true;
  try {
    await Promise.all([overviewStore.refresh(), rippleStore.refresh()]);
  } finally {
    refreshing.value = false;
  }
}
</script>

<style scoped>
.analytics-page {
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

.kpi-section,
.chart-section {
  width: 100%;
}

.section-title {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-accent);
}

.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.stats-row > * {
  flex: 1;
  min-width: 120px;
}

.production-summary {
  margin: var(--space-sm) 0 0;
  padding-left: 1.2em;
  font-size: 10px;
  font-family: monospace;
  line-height: 1.5;
}
</style>
