<!--
  CostBarChart.vue — Phase 8.7 + Phase 8.13 + F26
  Token 成本柱状图 (ECharts bar, by-scenario | by-tier)
  跟 CoolpointChart 同模式: dispose + re-init on watch, Press Start 2P 像素风
  color #ff6b6b 跟 Coolpoint 一致, 边框 #2a220f 像素风
  Phase 8.13: 加 mode toggle (scenario | tier) + costByTier 数据源
  F26: title + tier 配色/legend 跟 CostTrendChart 9.29 对齐
-->
<template>
  <div class="cost-bar-chart-wrapper pixel-border" data-testid="cost-bar-chart-wrapper">
    <h5 class="cost-bar-chart-title" data-testid="cost-bar-chart-title">📊 场景 / Tier 成本分布</h5>
    <div class="mode-tabs" role="tablist" aria-label="成本分类模式">
      <button
        type="button"
        role="tab"
        :class="['mode-tab', { active: mode === 'scenario' }]"
        :aria-selected="mode === 'scenario'"
        data-testid="mode-tab-scenario"
        @click="switchMode('scenario')"
      >By Scenario</button>
      <button
        type="button"
        role="tab"
        :class="['mode-tab', { active: mode === 'tier' }]"
        :aria-selected="mode === 'tier'"
        data-testid="mode-tab-tier"
        @click="switchMode('tier')"
      >By Tier</button>
    </div>
    <div ref="chartRef" class="cost-bar-chart" data-testid="cost-bar-chart" :style="{ width: '100%', height: '260px' }"></div>
    <p v-if="!hasData" class="cost-bar-chart-empty" data-testid="cost-bar-chart-empty">暂无成本数据</p>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { TIER_COLORS, TIER_ORDER, tierColor } from '../utils/costTrendChartUtils.js'

const props = defineProps({
  costByScenario: {
    type: Object,
    required: true,
    // shape: { "chapter_writing": 0.012, "chapter_review": 0.006, ... }
  },
  // Phase 8.13: tier 维度数据 (来自后端 cost_by_tier)
  // shape: { "premium": 0.05, "standard": 0.02, "budget": 0.005, ... }
  costByTier: {
    type: Object,
    default: () => ({}),
  },
  // Phase 8.13: 'scenario' | 'tier'
  mode: {
    type: String,
    default: 'scenario',
    validator: (v) => v === 'scenario' || v === 'tier',
  },
})

// Phase 8.13: 切 mode → 选数据源 (v-model:mode 走 update:mode)
const emit = defineEmits(['update:mode'])

const chartRef = ref(null)
let chartInstance = null

// Phase 8.13: displayData 根据 mode 选 costByScenario / costByTier
const displayData = computed(() => {
  return props.mode === 'tier' ? props.costByTier : props.costByScenario
})

const hasData = computed(() => {
  const data = displayData.value || {}
  return Object.keys(data).length > 0 && Object.values(data).some((v) => v > 0)
})

const isTierMode = computed(() => props.mode === 'tier')

// Phase 8.13: 切 mode 触发 update:mode (让 parent v-model:mode 接)
function switchMode(next) {
  if (next !== 'scenario' && next !== 'tier') return
  if (next === props.mode) return
  emit('update:mode', next)
}

const TOP_N = 12

const PIXEL_TOOLTIP = {
  trigger: 'axis',
  backgroundColor: '#2a220f',
  borderColor: '#2a220f',
  borderWidth: 2,
  textStyle: {
    fontFamily: 'Press Start 2P',
    fontSize: 13,
    color: '#fff7e8',
  },
}

function buildBarData(labels, costs) {
  const defaultColor = '#ff6b6b'
  return costs.map((value, index) => {
    const label = labels[index]
    const color = isTierMode.value ? tierColor(label) : defaultColor
    return {
      value,
      itemStyle: {
        color,
        borderColor: '#2a220f',
        borderWidth: 2,
      },
    }
  })
}

function tierLegendData(labels) {
  return TIER_ORDER.filter((tier) => labels.includes(tier))
}

function render() {
  if (!chartInstance) return
  if (!hasData.value) {
    chartInstance.clear()
    return
  }
  // sort by cost desc, top N
  const entries = Object.entries(displayData.value || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, TOP_N)
  const scenarios = entries.map(([k]) => k)
  const costs = entries.map(([, v]) => v)
  const barData = buildBarData(scenarios, costs)
  const legendData = isTierMode.value ? tierLegendData(scenarios) : []

  chartInstance.setOption({
    grid: { top: isTierMode.value ? 50 : 30, right: 20, bottom: 70, left: 70 },
    legend: isTierMode.value
      ? {
          data: legendData,
          top: 10,
          right: 10,
          textStyle: {
            fontFamily: 'Press Start 2P',
            fontSize: 13,
            color: '#2a220f',
          },
        }
      : undefined,
    tooltip: {
      ...PIXEL_TOOLTIP,
      formatter: (params) => {
        const p = params[0]
        const tierLabel = isTierMode.value ? ` (${p.name})` : ''
        return `${p.name}${tierLabel}<br/>成本: $${Number(p.value).toFixed(4)}`
      },
    },
    xAxis: {
      type: 'category',
      data: scenarios,
      axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
      axisTick: { lineStyle: { color: '#2a220f', width: 2 } },
      axisLabel: {
        rotate: 30,
        fontSize: 12,
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
        fontSize: 13,
        color: '#2a220f',
      },
      axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
      axisTick: { lineStyle: { color: '#2a220f', width: 2 } },
      axisLabel: {
        fontSize: 12,
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
        data: barData,
        barWidth: '60%',
        emphasis: {
          focus: 'self',
          itemStyle: {
            opacity: 1,
            borderWidth: 3,
          },
        },
        label: {
          show: true,
          position: 'top',
          fontFamily: 'Press Start 2P',
          fontSize: 12,
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

// Phase 8.13: watch displayData 覆盖 3 trigger (costByScenario 变 / costByTier 变 / mode 切)
watch(displayData, render, { deep: true })
watch(() => props.mode, render)
</script>

<style scoped>
.cost-bar-chart-wrapper {
  position: relative;
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  width: 100%;
  min-height: 280px;
}

.cost-bar-chart-title {
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-sm);
  color: var(--color-accent, #26a8ff);
  margin: 0 0 var(--space-sm) 0;
}

/* Phase 8.13: 模式切换 tabs (scenario | tier) */
.mode-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  border-bottom: 2px solid var(--border-color, #2a220f);
}

.mode-tab {
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  color: var(--color-text-dim, #b88230);
  transition: color 0.15s, border-color 0.15s;
}

.mode-tab:hover {
  color: var(--color-text, #2a220f);
}

.mode-tab.active {
  color: var(--color-accent, #26a8ff);
  border-bottom-color: var(--color-accent, #26a8ff);
  font-weight: bold;
}

.mode-tab:focus-visible {
  outline: 2px solid var(--color-accent, #26a8ff);
  outline-offset: 2px;
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
  font-size: var(--text-md);
  color: var(--color-text-dim, #b88230);
  text-align: center;
  padding: 16px;
  margin: 0;
}
</style>
