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

    <section class="kpi-section" data-testid="production-rollup-kpi">
      <h2 class="section-title">生产记录汇总</h2>
      <div class="stats-row">
        <StatCard
          v-for="card in productionRollupKpiCards"
          :key="card.label"
          :label="card.label"
          :value="card.value"
        />
      </div>
      <ul
        v-if="productionRollupLines.length"
        class="production-summary"
        data-testid="analytics-production-rollup-summary"
      >
        <li v-for="(line, idx) in productionRollupLines" :key="idx">{{ line }}</li>
      </ul>
      <table
        v-if="batchRollupRows.length"
        class="rollup-table"
        data-testid="analytics-batch-rollup-table"
      >
        <thead>
          <tr>
            <th>范围</th>
            <th>成本</th>
            <th>状态</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in batchRollupRows" :key="row.key">
            <td>{{ row.range }}</td>
            <td>{{ row.cost }}</td>
            <td>{{ row.status }}</td>
            <td>{{ row.at }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty-hint" data-testid="analytics-batch-rollup-empty">
        暂无 batch 记录（pilot/batch JSON 写入 infra/.state/pilot_records/）
      </p>
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
import { computed, onMounted, ref } from 'vue';
import StatCard from '../components/StatCard.vue';
import HookTrendChart from '../components/HookTrendChart.vue';
import CoolpointChart from '../components/CoolpointChart.vue';
import { fetchProductionRollup } from '../api/index.js';
import { useOverviewStore } from '../composables/useOverviewStore.js';
import { useRippleStore } from '../composables/useRippleStore.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';
import {
  buildProductionKpiCards,
  buildRippleKpiCards,
} from '../utils/analyticsKpi.js';
import {
  buildProductionRollupKpiCards,
  formatBatchRollupRows,
  productionRollupSummaryLines,
} from '../utils/analyticsProductionRollup.js';
import {
  productionSummaryLines,
  resolveProductionSummary,
} from '../utils/productionSummary.js';

const overviewStore = useOverviewStore();
const rippleStore = useRippleStore();
const { status } = useWorkflowSocket();

const refreshing = ref(false);
const rollupError = ref(null);
const productionRollup = ref(null);

const errorMessage = computed(() =>
  rollupError.value
  || overviewStore.lastError.value
  || rippleStore.lastError.value
  || null,
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
const productionRollupKpiCards = computed(() =>
  buildProductionRollupKpiCards(productionRollup.value),
);
const productionRollupLines = computed(() =>
  productionRollupSummaryLines(productionRollup.value),
);
const batchRollupRows = computed(() => formatBatchRollupRows(productionRollup.value));

async function loadProductionRollup() {
  rollupError.value = null;
  try {
    productionRollup.value = await fetchProductionRollup({ limit: 100 });
  } catch (e) {
    rollupError.value = e instanceof Error ? e.message : String(e);
  }
}

async function refreshAll() {
  refreshing.value = true;
  try {
    await Promise.all([
      overviewStore.refresh(),
      rippleStore.refresh(),
      loadProductionRollup(),
    ]);
  } finally {
    refreshing.value = false;
  }
}

onMounted(() => {
  loadProductionRollup();
});
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

.rollup-table {
  width: 100%;
  margin-top: var(--space-sm);
  border-collapse: collapse;
  font-size: 10px;
  font-family: monospace;
}

.rollup-table th,
.rollup-table td {
  border: 1px solid var(--border-color);
  padding: 6px 8px;
  text-align: left;
}

.rollup-table th {
  background: var(--bg-primary);
  font-family: 'Press Start 2P', monospace;
  font-size: 8px;
}

.empty-hint {
  font-size: 10px;
  font-family: monospace;
  opacity: 0.8;
  margin: var(--space-sm) 0 0;
}
</style>
