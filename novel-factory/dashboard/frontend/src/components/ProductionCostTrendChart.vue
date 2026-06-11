<template>
  <div class="production-cost-trend-chart pixel-border" data-testid="production-cost-trend-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as echarts from 'echarts';
import { buildCostTrendChartOption, hasCostTrendData } from '../utils/analyticsProductionCostTrend.js';

const props = defineProps({
  trend: {
    type: Object,
    default: null,
  },
});

const chartRef = ref(null);
let chartInstance = null;

const renderChart = () => {
  if (!chartRef.value || !hasCostTrendData(props.trend)) {
    destroyChart();
    return;
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  const option = buildCostTrendChartOption(props.trend);
  chartInstance.setOption(option, true);
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
}, { deep: true });
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
