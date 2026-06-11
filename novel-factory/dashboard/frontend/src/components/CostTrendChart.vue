<!--
  CostTrendChart.vue — Phase 8.24 + 8.29
  Token 成本时间序列折线图 (ECharts line, by-day UTC date → USD)
  跟 CostBarChart 同模式: dispose + re-init on watch, Press Start 2P 像素风
  color #ff6b6b 跟 CostBarChart 一致, 边框 #2a220f 像素风
  Phase 8.24: 接收 costByDay dict (Phase 8.23 后端), 按 UTC 日期升序 render
  empty 走 CostBarChart 同样 center "暂无 trend 数据" 提示
  跟 useCostWindow 集成: windowedCost 走 cost_by_day 透传 (Phase 8.18+ URL 同步)
  Phase 8.29: per-tier 趋势线 — 加 costByDayPerTier prop (additive, default null)
  shape: { "2026-06-01": { haiku: 0.005, sonnet: 0.015, opus: 0.020 }, ... }
  非空时切换 multi-series (3 lines: haiku/sonnet/opus) + ECharts legend.
  配色: haiku #67c23a (绿, 便宜) / sonnet #ff6b6b (红, 主力) / opus #9b59b6 (紫, 贵)
  backend 提供 cost_by_day_per_tier 聚合 (Phase 9.28 F12); prop default null 时走单线 path.
  Phase 9.29 F13: 单线 path 加累计折线 (跟每日线互补, ECharts legend 每日/累计).
-->
<template>
  <div class="cost-trend-chart-wrapper pixel-border" data-testid="cost-trend-chart-wrapper">
    <h5 class="cost-trend-chart-title" data-testid="cost-trend-chart-title">📈 每日 / 累计成本 trend</h5>
    <div ref="chartRef" class="cost-trend-chart" data-testid="cost-trend-chart" :style="{ width: '100%', height: '220px' }"></div>
    <p v-if="!hasData" class="cost-trend-chart-empty" data-testid="cost-trend-chart-empty">暂无 trend 数据</p>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import {
  computeCumulativeSeries,
  TIER_COLORS,
  TIER_ORDER,
} from '../utils/costTrendChartUtils.js'

const props = defineProps({
  // Phase 8.24: costByDay from backend cost_by_day (Phase 8.23)
  // shape: { "2026-06-01": 0.0105, "2026-06-02": 0.00525, ... }
  costByDay: {
    type: Object,
    required: true,
  },
  // Phase 8.29: per-day-per-tier breakdown (additive, default null)
  // shape: { "2026-06-01": { haiku: 0.005, sonnet: 0.015, opus: 0.020 }, ... }
  // 当非空时, render multi-series (3 lines) + ECharts legend, 覆盖单线 baseline
  costByDayPerTier: {
    type: Object,
    default: null,
  },
})

// Phase 8.29: per-tier mode gate (costByDayPerTier 非空且有非零 value → multi-series)
const hasMultiSeries = computed(() => {
  if (!props.costByDayPerTier) return false
  for (const dateKey of Object.keys(props.costByDayPerTier)) {
    const tierMap = props.costByDayPerTier[dateKey]
    if (tierMap && Object.values(tierMap).some((v) => v > 0)) return true
  }
  return false
})

const chartRef = ref(null)
let chartInstance = null

// Phase 8.24: hasData 走 CostBarChart 同样 pattern; Phase 9.28 F12: OR hasMultiSeries
const hasData = computed(() => {
  if (hasMultiSeries.value) return true
  const data = props.costByDay || {}
  return Object.keys(data).length > 0 && Object.values(data).some((v) => v > 0)
})

function render() {
  if (!chartInstance) return
  if (!hasData.value && !hasMultiSeries.value) {
    chartInstance.clear()
    return
  }

  // Phase 8.29: per-tier multi-series path (优先 over 单线)
  if (hasMultiSeries.value) {
    renderPerTier()
  } else {
    renderTotal()
  }
}

// Phase 8.29: multi-series 渲染 (per-day per-tier breakdown)
function renderPerTier() {
  const entries = Object.entries(props.costByDayPerTier || {})
    .sort(([a], [b]) => a.localeCompare(b))
  const dates = entries.map(([k]) => k)
  const series = TIER_ORDER
    .filter((tier) => entries.some(([, m]) => m && m[tier] > 0))  // 只渲染有数据的 tier
    .map((tier) => ({
      name: tier,
      type: 'line',
      data: entries.map(([, m]) => Number(m?.[tier] ?? 0)),
      symbol: 'rect',
      symbolSize: 6,
      lineStyle: { color: TIER_COLORS[tier], width: 2 },
      itemStyle: { color: TIER_COLORS[tier], borderColor: '#2a220f', borderWidth: 2 },
      smooth: false,
    }))

  chartInstance.setOption({
    grid: { top: 50, right: 20, bottom: 50, left: 70 },
    legend: {
      data: series.map((s) => s.name),
      top: 10,
      right: 10,
      textStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 8,
        color: '#2a220f',
      },
    },
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
      nameTextStyle: { fontFamily: 'Press Start 2P', fontSize: 8, color: '#2a220f' },
      axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
      axisTick: { lineStyle: { color: '#2a220f', width: 2 } },
      axisLabel: {
        fontSize: 7,
        fontFamily: 'Press Start 2P',
        color: '#2a220f',
        formatter: (v) => `$${Number(v).toFixed(4)}`,
      },
      splitLine: { lineStyle: { color: '#2a220f', width: 1, type: 'dashed' } },
    },
    series,
  })
}

// Phase 8.24 + F13: single-line path — daily + cumulative series
function renderTotal() {
  const entries = Object.entries(props.costByDay || {})
    .sort(([a], [b]) => a.localeCompare(b))
  const dates = entries.map(([k]) => k)
  const costs = entries.map(([, v]) => v)
  const cumulative = computeCumulativeSeries(costs)

  chartInstance.setOption({
    grid: { top: 50, right: 20, bottom: 50, left: 70 },
    legend: {
      data: ['每日', '累计'],
      top: 10,
      right: 10,
      textStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 8,
        color: '#2a220f',
      },
    },
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
        const lines = params.map(
          (p) => `${p.seriesName}: $${Number(p.value).toFixed(4)}`,
        )
        return `${params[0]?.name ?? ''}<br/>${lines.join('<br/>')}`
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
        name: '每日',
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
      {
        name: '累计',
        type: 'line',
        data: cumulative,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          color: '#409eff',
          width: 2,
          type: 'dashed',
        },
        itemStyle: {
          color: '#409eff',
          borderColor: '#2a220f',
          borderWidth: 2,
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

// Phase 8.24 + 8.29: watch costByDay + costByDayPerTier (深 watch, dict 引用变就 re-render)
watch(() => [props.costByDay, props.costByDayPerTier], render, { deep: true })
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
