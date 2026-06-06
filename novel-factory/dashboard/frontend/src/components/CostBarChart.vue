<!--
  CostBarChart.vue — Phase 8.7
  Token 成本柱状图 (ECharts bar, by-scenario)
  跟 CoolpointChart 同模式: dispose + re-init on watch, Press Start 2P 像素风
  color #ff6b6b 跟 Coolpoint 一致, 边框 #2a220f 像素风
-->
<template>
  <div class="cost-bar-chart-wrapper pixel-border">
    <div ref="chartRef" class="cost-bar-chart" :style="{ width: '100%', height: '260px' }"></div>
    <p v-if="!hasData" class="cost-bar-chart-empty">暂无成本数据</p>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  costByScenario: {
    type: Object,
    required: true,
    // shape: { "chapter_writing": 0.012, "chapter_review": 0.006, ... }
  },
})

const chartRef = ref(null)
let chartInstance = null

const hasData = computed(() => {
  const data = props.costByScenario || {}
  return Object.keys(data).length > 0 && Object.values(data).some((v) => v > 0)
})

const TOP_N = 12

function render() {
  if (!chartInstance) return
  if (!hasData.value) {
    chartInstance.clear()
    return
  }
  // sort by cost desc, top N
  const entries = Object.entries(props.costByScenario || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, TOP_N)
  const scenarios = entries.map(([k]) => k)
  const costs = entries.map(([, v]) => v)

  chartInstance.setOption({
    grid: { top: 30, right: 20, bottom: 70, left: 70 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#2a220f',
      borderColor: '#2a220f',
      borderWidth: 2,
      textStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 8,
        color: '#fff7e8',
      },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>成本: $${Number(p.value).toFixed(4)}`
      },
    },
    xAxis: {
      type: 'category',
      data: scenarios,
      axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
      axisTick: { lineStyle: { color: '#2a220f', width: 2 } },
      axisLabel: {
        rotate: 30,
        fontSize: 7,
        fontFamily: 'Press Start 2P',
        color: '#2a220f',
        interval: 0,
      },
    },
    yAxis: {
      type: 'value',
      name: 'USD',
      nameLocation: 'end',
      nameGap: 8,
      nameTextStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 8,
        color: '#2a220f',
      },
      axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
      axisTick: { lineStyle: { color: '#2a220f', width: 2 } },
      axisLabel: {
        fontSize: 7,
        fontFamily: 'Press Start 2P',
        color: '#2a220f',
        formatter: (v) => `$${Number(v).toFixed(4)}`,
      },
      splitLine: {
        lineStyle: { color: '#2a220f', width: 1, type: 'dashed' },
      },
    },
    series: [
      {
        type: 'bar',
        data: costs,
        barWidth: '60%',
        itemStyle: {
          color: '#ff6b6b',
          borderColor: '#2a220f',
          borderWidth: 2,
        },
        label: {
          show: true,
          position: 'top',
          fontFamily: 'Press Start 2P',
          fontSize: 7,
          color: '#2a220f',
          formatter: (p) => `$${Number(p.value).toFixed(4)}`,
        },
      },
    ],
  })
}

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    render()
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

watch(() => props.costByScenario, render, { deep: true })
</script>

<style scoped>
.cost-bar-chart-wrapper {
  position: relative;
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  width: 100%;
  min-height: 280px;
}

.cost-bar-chart {
  width: 100%;
  height: 260px;
}

.cost-bar-chart-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: 'Press Start 2P', monospace;
  font-size: 10px;
  color: var(--color-text-dim, #b88230);
  text-align: center;
  padding: 16px;
  margin: 0;
}
</style>
