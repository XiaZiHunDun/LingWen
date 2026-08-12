<template>
  <div class="coolpoint-chart pixel-border" data-testid="coolpoint-chart">
    <div ref="barRef" class="chart-container bar-chart"></div>
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

const barRef = ref(null)
let barChart = null
let echartsModule = null

const initBarChart = async () => {
  if (!barRef.value || props.data.length === 0) return

  try {
    if (!echartsModule) {
      echartsModule = await import('echarts')
    }

    if (!echartsModule?.default?.init) {
      logger.warn('[CoolpointChart] ECharts module not properly loaded')
      return
    }

    if (barChart) {
      barChart.dispose()
    }

    barChart = echartsModule.default.init(barRef.value)

  const chapters = props.data.map(d => d.chapter)
  const coolpointCounts = props.data.map(d => d.coolpoint_count)

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
        return `第${params.data[0]}章<br/>爽点数: ${params.data[1]}`
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
      name: '爽点数',
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
        data: props.data.map(d => [d.chapter, d.coolpoint_count]),
        type: 'bar',
        barWidth: '60%',
        itemStyle: {
          color: '#ff6b6b',
          borderColor: '#2a220f',
          borderWidth: 2
        }
      }
    ]
  }

  barChart.setOption(option)
  } catch (error) {
    logger.warn('[CoolpointChart] Error initializing chart:', error)
  }
}

const destroyChart = () => {
  if (barChart) {
    barChart.dispose()
    barChart = null
  }
}

onMounted(async () => {
  await initBarChart()
})

onUnmounted(() => {
  destroyChart()
})

watch(() => props.data, async () => {
  await initBarChart()
}, { deep: true })
</script>

<style scoped>
.coolpoint-chart {
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  width: 100%;
  min-height: 220px;
}

.chart-container {
  width: 100%;
  height: 200px;
}
</style>