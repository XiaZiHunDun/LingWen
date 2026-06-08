<!--
  CostTrendChart.vue — Phase 8.24
  Token 成本时间序列折线图 (ECharts line, by-day UTC date → USD)
  跟 CostBarChart 同模式: dispose + re-init on watch, Press Start 2P 像素风
  color #ff6b6b 跟 CostBarChart 一致, 边框 #2a220f 像素风
  Phase 8.24: 接收 costByDay dict (Phase 8.23 后端), 按 UTC 日期升序 render
  empty 走 CostBarChart 同样 center "暂无 trend 数据" 提示
  跟 useCostWindow 集成: windowedCost 走 cost_by_day 透传 (Phase 8.18+ URL 同步)
-->
<template>
  <div class="cost-trend-chart-wrapper pixel-border" data-testid="cost-trend-chart-wrapper">
    <h5 class="cost-trend-chart-title">📈 每日成本 trend</h5>
    <div ref="chartRef" class="cost-trend-chart" data-testid="cost-trend-chart" :style="{ width: '100%', height: '220px' }"></div>
    <p v-if="!hasData" class="cost-trend-chart-empty" data-testid="cost-trend-chart-empty">暂无 trend 数据</p>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // Phase 8.24: costByDay from backend cost_by_day (Phase 8.23)
  // shape: { "2026-06-01": 0.0105, "2026-06-02": 0.00525, ... }
  costByDay: {
    type: Object,
    required: true,
  },
})

const chartRef = ref(null)
let chartInstance = null

// Phase 8.24: hasData 走 CostBarChart 同样 pattern (Object.keys + some > 0)
const hasData = computed(() => {
  const data = props.costByDay || {}
  return Object.keys(data).length > 0 && Object.values(data).some((v) => v > 0)
})

function render() {
  if (!chartInstance) return
  if (!hasData.value) {
    chartInstance.clear()
    return
  }
  // Phase 8.24: sort by date asc (后端 ORDER BY day 已升序, 防御性再排一次)
  const entries = Object.entries(props.costByDay || {})
    .sort(([a], [b]) => a.localeCompare(b))
  const dates = entries.map(([k]) => k)
  const costs = entries.map(([, v]) => v)

  chartInstance.setOption({
    grid: { top: 20, right: 20, bottom: 50, left: 70 },
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
      data: dates,
      axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
      axisTick: { lineStyle: { color: '#2a220f', width: 2 } },
      axisLabel: {
        rotate: 30,
        fontSize: 7,
        fontFamily: 'Press Start 2P',
        color: '#2a220f',
        interval: 'auto',
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
        type: 'line',
        data: costs,
        symbol: 'rect',
        symbolSize: 8,
        lineStyle: {
          color: '#ff6b6b',
          width: 2,
        },
        itemStyle: {
          color: '#ff6b6b',
          borderColor: '#2a220f',
          borderWidth: 2,
        },
        areaStyle: {
          color: 'rgba(255, 107, 107, 0.2)',
        },
        smooth: false,
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

// Phase 8.24: watch costByDay (深 watch, dict 引用变就 re-render)
watch(() => props.costByDay, render, { deep: true })
</script>

<style scoped>
.cost-trend-chart-wrapper {
  position: relative;
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  width: 100%;
  min-height: 240px;
}

.cost-trend-chart-title {
  font-family: 'Press Start 2P', monospace;
  font-size: 9px;
  color: var(--color-accent, #26a8ff);
  margin: 0 0 var(--space-sm) 0;
}

.cost-trend-chart {
  width: 100%;
  height: 220px;
}

.cost-trend-chart-empty {
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
