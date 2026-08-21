<template>
  <div class="production-cost-trend-chart pixel-border" data-testid="production-cost-trend-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { buildCostTrendChartOption, hasCostTrendData } from '../utils/analyticsProductionCostTrend.js';
import { logger } from '../utils/logger.js';

const props = defineProps({
  trend: {
    type: Object,
    default: null,
  },
});

const chartRef = ref(null);
let chartInstance = null;
let echartsModule = null;

const renderChart = async () => {
  if (!chartRef.value || !hasCostTrendData(props.trend)) {
    destroyChart();
    return;
  }

  try {
    if (!echartsModule) {
      echartsModule = await import('echarts');
    }

    if (!echartsModule?.default?.init) {
      logger.warn('[ProductionCostTrendChart] ECharts module not properly loaded');
      return;
    }

    if (!chartInstance) {
      chartInstance = echartsModule.default.init(chartRef.value);
    }

    const option = buildCostTrendChartOption(props.trend);
    chartInstance.setOption(option, true);
  } catch (error) {
    logger.warn('[ProductionCostTrendChart] Error rendering chart:', error);
  }
};

const destroyChart = () => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
};

onMounted(() => {
  renderChart();
});

onUnmounted(() => {
  destroyChart();
});

watch(() => props.trend, () => {
  renderChart();
});
</script>

<style scoped>
.production-cost-trend-chart {
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  width: 100%;
  min-height: 220px;
}

.chart-container {
  width: 100%;
  height: 220px;
}
</style>
