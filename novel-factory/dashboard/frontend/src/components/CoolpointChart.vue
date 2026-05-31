<template>
  <div class="coolpoint-chart pixel-border">
    <div ref="barRef" class="chart-container bar-chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const barRef = ref(null)
let barChart = null

const initBarChart = () => {
  if (!barRef.value || props.data.length === 0) return

  if (barChart) {
    barChart.dispose()
  }

  barChart = echarts.init(barRef.value)

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
        fontSize: 8,
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
        fontSize: 8,
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
        fontSize: 6,
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
        fontSize: 8,
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
        fontSize: 6,
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
}

const destroyChart = () => {
  if (barChart) {
    barChart.dispose()
    barChart = null
  }
}

onMounted(() => {
  initBarChart()
})

onUnmounted(() => {
  destroyChart()
})

watch(() => props.data, () => {
  initBarChart()
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