<template>
  <div class="coolpoint-chart pixel-border">
    <div class="chart-wrapper">
      <div ref="barRef" class="chart-container bar-chart"></div>
      <div ref="pieRef" class="chart-container pie-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  typeDistribution: {
    type: Object,
    default: () => {}
  }
})

const barRef = ref(null)
const pieRef = ref(null)
let barChart = null
let pieChart = null

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

const initPieChart = () => {
  if (!pieRef.value) return

  if (pieChart) {
    pieChart.dispose()
  }

  pieChart = echarts.init(pieRef.value)

  const types = Object.keys(props.typeDistribution)
  const values = Object.values(props.typeDistribution)

  if (types.length === 0) {
    pieChart.setOption({
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          fontFamily: 'Press Start 2P',
          fontSize: 8,
          color: '#2a220f'
        }
      }
    })
    return
  }

  const option = {
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
        return `${params.data.name}<br/>${params.data.value}次`
      }
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: {
        fontFamily: 'Press Start 2P',
        fontSize: 6,
        color: '#2a220f'
      }
    },
    series: [
      {
        data: types.map((name, i) => ({ name, value: values[i] })),
        type: 'pie',
        radius: ['30%', '70%'],
        center: ['35%', '50%'],
        itemStyle: {
          borderColor: '#2a220f',
          borderWidth: 2
        },
        label: {
          show: false
        }
      }
    ]
  }

  pieChart.setOption(option)
}

const destroyCharts = () => {
  if (barChart) {
    barChart.dispose()
    barChart = null
  }
  if (pieChart) {
    pieChart.dispose()
    pieChart = null
  }
}

onMounted(() => {
  initBarChart()
  initPieChart()
})

onUnmounted(() => {
  destroyCharts()
})

watch(() => props.data, () => {
  initBarChart()
}, { deep: true })

watch(() => props.typeDistribution, () => {
  initPieChart()
}, { deep: true })
</script>

<style scoped>
.coolpoint-chart {
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  width: 100%;
  min-height: 220px;
}

.chart-wrapper {
  display: flex;
  gap: var(--space-md);
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 200px;
}

.bar-chart {
  flex: 2;
}

.pie-chart {
  flex: 1;
  min-width: 180px;
}
</style>