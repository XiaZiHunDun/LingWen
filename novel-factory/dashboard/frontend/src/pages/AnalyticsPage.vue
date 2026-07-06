<!--
  AnalyticsPage.vue — Phase 9.77 F67: 数据分析 MVP
  - 追读力 charts (reuse Overview store + HookTrendChart / CoolpointChart)
  - 生产 KPI (WS workflow status + production_summary)
  - 涟漪统计 (useRippleStore stats)
-->
<template>
  <div class="analytics-page">
    <header v-if="!embedded" class="page-header">
      <div>
        <h1 class="page-title" data-testid="page-title">数据分析</h1>
        <p v-if="activeSlug" class="project-hint" data-testid="active-project-hint">
          当前项目：{{ activeSlug }}
        </p>
      </div>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="refreshing"
        @click="refreshAll"
      >
        {{ refreshing ? '加载中…' : '刷新' }}
      </button>
    </header>

    <p v-else-if="activeSlug" class="project-hint embedded-hint" data-testid="active-project-hint">
      当前项目：{{ activeSlug }}
    </p>

    <div v-if="displayError" class="error-banner pixel-border" data-testid="error-banner">
      {{ displayError }}
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
      <div
        v-if="productionRecordsDir && !isReadonlyInsight"
        class="records-dir-hint"
        data-testid="production-records-dir"
      >
        <details class="records-dir-details">
          <summary>数据来源（运维路径）</summary>
          <code>{{ productionRecordsDir }}</code>
        </details>
      </div>
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
        暂无 batch 记录（切换顶栏项目后自动加载对应 pilot_records）
      </p>
    </section>

    <section class="kpi-section" data-testid="production-cost-trend-kpi">
      <h2 class="section-title">生产成本趋势</h2>
      <ul
        v-if="productionCostTrendLines.length"
        class="production-summary"
        data-testid="analytics-production-cost-trend-summary"
      >
        <li v-for="(line, idx) in productionCostTrendLines" :key="idx">{{ line }}</li>
      </ul>
      <ProductionCostTrendChart
        v-if="hasProductionCostTrend"
        :trend="productionCostTrend"
      />
      <p v-else class="empty-hint" data-testid="analytics-production-cost-trend-empty">
        暂无带时间的生产记录（写入 pilot/batch JSON 后按 recorded_at 展示）
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
import { computed, inject, onMounted, ref, watch } from 'vue';
import StatCard from '../components/StatCard.vue';
import HookTrendChart from '../components/HookTrendChart.vue';
import CoolpointChart from '../components/CoolpointChart.vue';
import ProductionCostTrendChart from '../components/ProductionCostTrendChart.vue';
import { fetchProductionCostTrend, fetchProductionRollup } from '../api/index.js';
import { useOverviewStore } from '../composables/useOverviewStore.js';
import { useRippleStore } from '../composables/useRippleStore.js';
import { useStudioProject } from '../composables/useStudioProject.js';
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
  hasCostTrendData,
  productionCostTrendSummaryLines,
} from '../utils/analyticsProductionCostTrend.js';
import {
  productionSummaryLines,
  resolveProductionSummary,
} from '../utils/productionSummary.js';
import { useFilteredPageError } from '../composables/useFilteredPageError.js';

defineProps({
  embedded: { type: Boolean, default: false },
});

const isReadonlyInsight = inject('isReadonlyInsight', computed(() => false));

const overviewStore = useOverviewStore();
const rippleStore = useRippleStore();
const { status } = useWorkflowSocket();
const { activeSlug, projectRevision } = useStudioProject();

const refreshing = ref(false);
const rollupError = ref(null);
const trendError = ref(null);
const productionRollup = ref(null);
const productionCostTrend = ref(null);

const errorMessage = computed(() =>
  rollupError.value
  || trendError.value
  || overviewStore.lastError.value
  || rippleStore.lastError.value
  || null,
);
const displayError = useFilteredPageError(errorMessage);

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
const productionRecordsDir = computed(
  () => productionRollup.value?.records_dir
    || productionCostTrend.value?.records_dir
    || null,
);
const hasProductionCostTrend = computed(() => hasCostTrendData(productionCostTrend.value));
const productionCostTrendLines = computed(() =>
  productionCostTrendSummaryLines(productionCostTrend.value),
);

async function loadProductionRollup() {
  rollupError.value = null;
  try {
    productionRollup.value = await fetchProductionRollup({ limit: 100 });
  } catch (e) {
    rollupError.value = e instanceof Error ? e.message : String(e);
  }
}

async function loadProductionCostTrend() {
  trendError.value = null;
  try {
    productionCostTrend.value = await fetchProductionCostTrend({ limit: 100 });
  } catch (e) {
    trendError.value = e instanceof Error ? e.message : String(e);
  }
}

async function refreshAll() {
  refreshing.value = true;
  try {
    await Promise.all([
      overviewStore.refresh(),
      rippleStore.refresh(),
      loadProductionRollup(),
      loadProductionCostTrend(),
    ]);
  } finally {
    refreshing.value = false;
  }
}

onMounted(() => {
  loadProductionRollup();
  loadProductionCostTrend();
});

watch(projectRevision, () => {
  loadProductionRollup();
  loadProductionCostTrend();
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
  font-size: var(--text-xl);
  font-weight: bold;
  color: var(--color-text);
  font-family: var(--font-ui);
}

.project-hint {
  font-size: var(--text-sm);
  font-family: monospace;
  margin: var(--space-xs) 0 0;
  opacity: 0.85;
}

.records-dir-hint {
  font-size: var(--text-sm);
  font-family: monospace;
  margin: 0 0 var(--space-sm);
  opacity: 0.9;
  word-break: break-all;
}

.records-dir-hint code {
  font-size: var(--text-sm);
}

.refresh-btn {
  background-color: var(--bg-secondary);
  color: var(--color-text);
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-sm);
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
  font-size: var(--text-sm);
  font-family: 'Press Start 2P', monospace;
}

.kpi-section,
.chart-section {
  width: 100%;
}

.section-title {
  font-size: var(--text-lg);
  font-family: var(--font-ui);
  font-weight: 600;
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
  font-size: var(--text-sm);
  font-family: monospace;
  line-height: 1.5;
}

.rollup-table {
  width: 100%;
  margin-top: var(--space-sm);
  border-collapse: collapse;
  font-size: var(--text-sm);
  font-family: monospace;
}

.rollup-table th,
.rollup-table td {
  border: 1px solid var(--border-color);
  padding: 10px 12px;
  text-align: left;
}

.rollup-table th {
  background: var(--bg-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
}

.records-dir-details summary {
  cursor: pointer;
  color: var(--color-accent);
  font-weight: 500;
}

.records-dir-details code {
  display: block;
  margin-top: var(--space-xs);
  word-break: break-all;
}

.empty-hint {
  font-size: var(--text-sm);
  font-family: monospace;
  opacity: 0.8;
  margin: var(--space-sm) 0 0;
}
</style>
