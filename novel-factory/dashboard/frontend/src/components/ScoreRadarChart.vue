<template>
  <div class="score-radar-chart">
    <h4 class="radar-title">S1-S8 评分对比</h4>

    <div v-if="fallback" class="score-radar-fallback-warning">
      ⚠️ LLM 评分未生效, 兜底: {{ fallback }}
    </div>

    <div ref="chartRef" class="radar-canvas"></div>

    <div v-if="winner" class="winner-badge">
      🏆 优胜: <strong>{{ winnerLabel }}</strong>
      <span class="delta">(Δ {{ deltaText }})</span>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  scoresA: { type: Object, required: true },
  scoresB: { type: Object, required: true },
  labelA: { type: String, default: 'Variant A' },
  labelB: { type: String, default: 'Variant B' },
  winner: { type: String, default: '' },
  fallback: { type: String, default: null },
})

const chartRef = ref(null)
let chartInstance = null

const S1_S8 = [
  { key: 'S1', name: 'S1 剧情', max: 10 },
  { key: 'S2', name: 'S2 逻辑', max: 10 },
  { key: 'S3', name: 'S3 文笔', max: 10 },
  { key: 'S4', name: 'S4 情感', max: 10 },
  { key: 'S5', name: 'S5 节奏', max: 10 },
  { key: 'S6', name: 'S6 可读', max: 10 },
  { key: 'S7', name: 'S7 主角', max: 10 },
  { key: 'S8', name: 'S8 弧光', max: 10 },
]

const valuesA = computed(() => S1_S8.map(d => props.scoresA[d.key] ?? 0))
const valuesB = computed(() => S1_S8.map(d => props.scoresB[d.key] ?? 0))

const winnerLabel = computed(() => {
  if (props.winner === props.labelA) return props.labelA
  if (props.winner === props.labelB) return props.labelB
  return props.winner || '—'
})

const deltaText = computed(() => {
  const delta = (valuesA.value.reduce((a, b) => a + b, 0) - valuesB.value.reduce((a, b) => a + b, 0)) / 8
  return delta > 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)
})

function render() {
  if (!chartInstance) return
  const isAWinner = props.winner === props.labelA
  const isBWinner = props.winner === props.labelB

  chartInstance.setOption({
    tooltip: { trigger: 'item' },
    legend: { data: [props.labelA, props.labelB], top: 0 },
    radar: {
      indicator: S1_S8,
      shape: 'polygon',
      splitNumber: 5,
      axisName: { color: '#555', fontSize: 11 },
    },
    series: [{
      type: 'radar',
      data: [
        {
          name: props.labelA,
          value: valuesA.value,
          itemStyle: { color: isAWinner ? '#67c23a' : '#909399' },
          lineStyle: { color: isAWinner ? '#67c23a' : '#909399', width: 2 },
          areaStyle: { color: isAWinner ? 'rgba(103,194,58,0.3)' : 'rgba(144,143,153,0.1)' },
        },
        {
          name: props.labelB,
          value: valuesB.value,
          itemStyle: { color: isBWinner ? '#67c23a' : '#909399' },
          lineStyle: { color: isBWinner ? '#67c23a' : '#909399', width: 2 },
          areaStyle: { color: isBWinner ? 'rgba(103,194,58,0.3)' : 'rgba(144,143,153,0.1)' },
        },
      ],
    }],
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

watch([() => props.scoresA, () => props.scoresB, () => props.winner], render, { deep: true })
</script>

<style scoped>
.score-radar-chart {
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #67c23a;
  border-radius: 4px;
  padding: 12px;
  margin: 12px 0;
  font-family: 'Press Start 2P', monospace;
}
.radar-title {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #333;
  text-align: center;
}
.radar-canvas {
  width: 100%;
  height: 320px;
}
.score-radar-fallback-warning {
  background: #fdf6ec;
  color: #b88230;
  border-left: 3px solid #e6a23c;
  padding: 6px 10px;
  font-size: 10px;
  margin-bottom: 8px;
}
.winner-badge {
  text-align: center;
  font-size: 10px;
  color: #67c23a;
  margin-top: 4px;
}
.winner-badge .delta {
  color: #909399;
  margin-left: 4px;
}
</style>
