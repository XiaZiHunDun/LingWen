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
        <p v-if="activeSlug" class="project-hint active-project-hint" data-testid="active-project-hint">
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

    <p v-else-if="activeSlug" class="project-hint embedded-hint active-project-hint" data-testid="active-project-hint">
      当前项目：{{ activeSlug }}
    </p>

    <div v-if="displayError" class="error-banner pixel-border" data-testid="error-banner">
      {{ displayError }}
    </div>

    <section class="kpi-section batch-progress-kpi" data-testid="batch-progress-kpi">
      <h2 class="section-title">当前生产 Batch 进度</h2>
      <p
        v-if="!batch.activeJob.value"
        class="empty-hint analytics-batch-progress-empty"
        data-testid="analytics-batch-progress-empty"
      >
        无进行中的 batch（可在生产 / Pilot 页发起）
      </p>
      <div v-else class="batch-progress analytics-batch-progress" data-testid="analytics-batch-progress">
        <div class="batch-progress-row">
          <span class="batch-progress-label">状态:</span>
          <strong :class="`batch-status-${batch.activeJob.value.status}`">{{ batch.activeJob.value.status }}</strong>
          <span v-if="batch.isConnected.value" class="batch-progress-live analytics-batch-progress-live" data-testid="analytics-batch-progress-live">● 实时</span>
          <span class="batch-progress-range">{{ batchRange }}</span>
          <span v-if="batch.activeJob.value.budget_usd != null" class="batch-progress-budget">${{ batch.activeJob.value.budget_usd }}</span>
          <span v-if="batch.activeJob.value.pid" class="batch-progress-pid">pid: {{ batch.activeJob.value.pid }}</span>
        </div>
        <div class="batch-progress-stage analytics-batch-progress-stage" data-testid="analytics-batch-progress-stage">
          已完成 {{ batchCompletedCount }} / {{ batchTotalChapters }} 章
        </div>
        <ul
          v-if="batchChapterItems.length"
          class="batch-progress-chapters analytics-batch-progress-chapters"
          data-testid="analytics-batch-progress-chapters"
        >
          <li v-for="item in batchChapterItems" :key="`${item.chapter_num}-${item.receivedAt}`">
            ch{{ String(item.chapter_num).padStart(3, '0') }}
          </li>
        </ul>
      </div>
    </section>

    <section class="kpi-section production-kpi" data-testid="production-kpi">
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
        class="production-summary analytics-production-summary"
        data-testid="analytics-production-summary"
      >
        <li v-for="(line, idx) in productionLines" :key="idx">{{ line }}</li>
      </ul>
    </section>

    <section class="kpi-section production-rollup-kpi" data-testid="production-rollup-kpi">
      <h2 class="section-title">生产记录汇总</h2>
      <div
        v-if="productionRecordsDir && !isReadonlyInsight"
        class="records-dir-hint production-records-dir"
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
        class="production-summary analytics-production-rollup-summary"
        data-testid="analytics-production-rollup-summary"
      >
        <li v-for="(line, idx) in productionRollupLines" :key="idx">{{ line }}</li>
      </ul>
      <table
        v-if="batchRollupRows.length"
        class="rollup-table analytics-batch-rollup-table"
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
      <p v-else class="empty-hint analytics-batch-rollup-empty" data-testid="analytics-batch-rollup-empty">
        暂无 batch 记录（切换顶栏项目后自动加载对应 pilot_records）
      </p>
    </section>

    <section class="kpi-section production-cost-trend-kpi" data-testid="production-cost-trend-kpi">
      <h2 class="section-title">生产成本趋势</h2>
      <ul
        v-if="productionCostTrendLines.length"
        class="production-summary analytics-production-cost-trend-summary"
        data-testid="analytics-production-cost-trend-summary"
      >
        <li v-for="(line, idx) in productionCostTrendLines" :key="idx">{{ line }}</li>
      </ul>
      <ProductionCostTrendChart
        v-if="hasProductionCostTrend"
        :trend="productionCostTrend"
      />
      <p v-else class="empty-hint analytics-production-cost-trend-empty" data-testid="analytics-production-cost-trend-empty">
        暂无带时间的生产记录（写入 pilot/batch JSON 后按 recorded_at 展示）
      </p>
    </section>

    <section class="kpi-section ripple-kpi" data-testid="ripple-kpi">
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
import { fetchProductionCostTrend, fetchProductionRollup } from '@/api/health';
import { useOverviewStore, useRippleStore, useStudioProject, useWorkflowSocket, useFilteredPageError } from '../composables/index.js';
import { usePilotBatch } from '../composables/usePilotBatch';
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

defineProps({
  embedded: { type: Boolean, default: false },
});

const isReadonlyInsight = inject('isReadonlyInsight', computed(() => false));

const overviewStore = useOverviewStore();
const rippleStore = useRippleStore();
const { status } = useWorkflowSocket();
const { activeSlug, projectRevision } = useStudioProject();

// P2-INSIGHT: 复用 usePilotBatch 把实时 batch 进度汇入主看板（只读展示）。
const batch = usePilotBatch();

const batchTotalChapters = computed(() => {
  const a = batch.activeJob.value;
  if (!a) return 0;
  return (a.end_chapter ?? 0) - (a.start_chapter ?? 0) + 1;
});

const batchCompletedCount = computed(() => {
  const done = new Set(batch.chapterEvents.value.map((e) => e.chapter_num));
  return done.size;
});

const batchRange = computed(() => {
  const a = batch.activeJob.value;
  if (!a) return '';
  return `ch${String(a.start_chapter).padStart(3, '0')}–ch${String(a.end_chapter).padStart(3, '0')}`;
});

const batchChapterItems = computed(() => batch.chapterEvents.value.slice(-8));

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
  void batch.refreshActive();
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
.batch-progress { display: flex; flex-direction: column; gap: var(--space-sm); font-family: monospace; font-size: var(--text-sm); }
.batch-progress-row { display: flex; gap: var(--space-md); align-items: center; flex-wrap: wrap; }
.batch-progress-label { opacity: 0.8; }
.batch-status-running { color: var(--color-success, #2c7a2c); font-weight: 600; }
.batch-status-completed { color: var(--color-accent); font-weight: 600; }
.batch-status-failed, .batch-status-cancelled { color: var(--color-danger, #c33); font-weight: 600; }
.batch-progress-live { font-size: var(--text-xs); color: var(--color-success, #2c7a2c); border: 1px solid currentColor; border-radius: 999px; padding: 0 var(--space-sm); }
.batch-progress-range, .batch-progress-budget, .batch-progress-pid { opacity: 0.85; }
.batch-progress-stage { opacity: 0.9; }
.batch-progress-chapters { list-style: none; display: flex; flex-wrap: wrap; gap: var(--space-sm); margin: 0; padding: 0; }
.batch-progress-chapters li { background: var(--bg-secondary); border-radius: var(--radius-sm); padding: var(--space-xs) var(--space-sm); }
</style>
