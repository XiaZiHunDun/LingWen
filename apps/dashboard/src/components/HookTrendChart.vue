<template>
  <div class="hook-trend-chart pixel-border" data-testid="hook-trend-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { logger } from '../utils/logger.js'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null
let echartsModule = null

const initChart = async () => {
  if (!chartRef.value || props.data.length === 0) return

  try {
    if (!echartsModule) {
      echartsModule = await import('echarts')
    }

    if (!echartsModule?.default?.init) {
      logger.warn('[HookTrendChart] ECharts module not properly loaded')
      return
    }

    chartInstance = echartsModule.default.init(chartRef.value)

  const chapters = props.data.map(d => d.chapter)
  const hookCounts = props.data.map(d => d.hook_count)

  const option = {
    grid: {
      top: 30,
      right: 20,
      bottom: 40,
      left: 50
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#2a220f',
      borderColor: '#2a220f',
      borderWidth: 2,
      textStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 13,
        color: '#fff7e8'
      },
      formatter: (params) => {
        return `Ch ${params.data[0]}<br/>钩子数: ${params.data[1]}`
      }
    },
    xAxis: {
      type: 'category',
      data: chapters,
      name: '章节',
      nameLocation: 'end',
      nameGap: 8,
      nameTextStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 13,
        color: '#2a220f'
      },
      axisLine: {
        lineStyle: { color: '#2a220f', width: 2 }
      },
      axisTick: {
        lineStyle: { color: '#2a220f', width: 2 }
      },
      axisLabel: {
        fontFamily: 'Press Start 2P',
        fontSize: 12,
        color: '#2a220f'
      }
    },
    yAxis: {
      type: 'value',
      name: '钩子数',
      nameLocation: 'end',
      nameGap: 8,
      nameTextStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 13,
        color: '#2a220f'
      },
      axisLine: {
        lineStyle: { color: '#2a220f', width: 2 }
      },
      axisTick: {
        lineStyle: { color: '#2a220f', width: 2 }
      },
      axisLabel: {
        fontFamily: 'Press Start 2P',
        fontSize: 12,
        color: '#2a220f'
      },
      splitLine: {
        lineStyle: {
          color: '#2a220f',
          width: 1,
          type: 'dashed'
        }
      }
    },
    series: [
      {
        data: props.data.map(d => [d.chapter, d.hook_count]),
        type: 'line',
        smooth: false,
        symbol: 'square',
        symbolSize: 6,
        lineStyle: {
          color: '#26a8ff',
          width: 3
        },
        itemStyle: {
          color: '#26a8ff',
          borderColor: '#2a220f',
          borderWidth: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(38, 168, 255, 0.4)' },
              { offset: 1, color: 'rgba(38, 168, 255, 0.05)' }
            ]
          }
        }
      }
    ]
  }

  chartInstance.setOption(option)
  } catch (error) {
    logger.warn('[HookTrendChart] Error initializing chart:', error)
  }
}

const destroyChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

onMounted(async () => {
  await initChart()
})

onUnmounted(() => {
  destroyChart()
})

watch(() => props.data, async () => {
  await initChart()
}, { deep: true })
</script>

<style scoped>
.hook-trend-chart {
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  width: 100%;
  min-height: 200px;
}

.chart-container {
  width: 100%;
  height: 200px;
}
</style>