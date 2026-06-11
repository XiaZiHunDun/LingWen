<!--
  ImpactGraph.vue — Phase 9.41 F30
  CVG reference graph (reference_nodes + reference_edges) ECharts force layout.
  Pattern mirrors CascadeGraph.vue: lazy ECharts, roam, emphasis, nodeClick emit.
-->
<template>
  <div class="impact-graph-wrapper" data-testid="impact-graph-wrapper">
    <h5 class="impact-graph-title" data-testid="impact-graph-title">
      🌐 跨卷 reference graph
      <span v-if="graph && graph.total_node_count" class="impact-graph-count">
        ({{ graph.nodes.length }}/{{ graph.total_node_count }} nodes)
      </span>
    </h5>
    <div
      v-if="hasData"
      class="impact-graph"
      data-testid="impact-graph"
      :data-node-count="graph.nodes.length"
    >
      <div ref="chartEl" class="impact-graph__chart" data-testid="impact-graph-chart"></div>
      <div
        v-if="graph.truncated"
        class="impact-graph__warning"
        data-testid="impact-graph-warning"
      >
        Truncated to first {{ graph.nodes.length }} nodes
      </div>
    </div>
    <div v-else class="impact-graph-empty" data-testid="impact-graph-empty">
      暂无 reference graph 数据
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { impactNodeColor, IMPACT_DIMENSION_ORDER } from '../utils/impactGraphUtils.js'

const props = defineProps({
  graph: { type: Object, default: null },
})

const emit = defineEmits(['nodeClick'])

const chartEl = ref(null)
let chart = null

const hasData = computed(() => {
  const g = props.graph
  return Boolean(g && Array.isArray(g.nodes) && g.nodes.length > 0)
})

function nodeLabel(node) {
  const title = node.title || node.id
  return `${title} (V${node.volume}c${node.chapter})`
}

function legendDimensions(nodes) {
  const present = new Set(nodes.map((n) => n.dimension))
  return IMPACT_DIMENSION_ORDER.filter((d) => present.has(d))
}

async function initChart() {
  if (!chartEl.value || !hasData.value) {
    if (chart) {
      chart.clear()
    }
    return
  }
  const echarts = await import('echarts/core')
  const { GraphChart } = await import('echarts/charts')
  const { TitleComponent, TooltipComponent, LegendComponent } = await import('echarts/components')
  const { CanvasRenderer } = await import('echarts/renderers')
  echarts.use([GraphChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

  if (!chart) {
    chart = echarts.init(chartEl.value)
    chart.on('click', (params) => {
      if (params.dataType === 'node') {
        const n = props.graph.nodes.find((x) => x.id === params.data.id)
        if (n) {
          emit('nodeClick', {
            nodeId: n.id,
            volume: n.volume,
            chapter: n.chapter,
            dimension: n.dimension,
          })
        }
      }
    })
  }

  const nodes = props.graph.nodes.map((n) => ({
    id: n.id,
    name: nodeLabel(n),
    symbolSize: 28,
    itemStyle: { color: impactNodeColor(n.dimension) },
    category: n.dimension,
  }))
  const edges = (props.graph.edges || []).map((e) => ({
    source: e.from_node_id,
    target: e.to_node_id,
    lineStyle: { width: 1 + (e.weight ?? 0) * 2, opacity: 0.6 + (e.weight ?? 0) * 0.4 },
  }))
  const legendData = legendDimensions(props.graph.nodes)

  chart.setOption({
    grid: { top: 50, right: 20, bottom: 20, left: 20 },
    legend: {
      data: legendData,
      top: 8,
      right: 8,
      textStyle: { fontSize: 10, color: '#2a220f' },
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}`
        }
        const n = props.graph.nodes.find((x) => x.id === params.data.id)
        if (!n) return params.name
        return [
          n.dimension,
          `V${n.volume} ch${n.chapter}`,
          n.description || n.title || n.id,
        ].join('<br/>')
      },
    },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      categories: legendData.map((name) => ({ name })),
      data: nodes,
      edges,
      force: { repulsion: 120, edgeLength: 80 },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 },
      },
      label: { show: false },
    }],
  })
}

onMounted(initChart)
onUnmounted(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
})
watch(() => props.graph, initChart, { deep: true })

defineExpose({ impactNodeColor })
</script>

<style scoped>
.impact-graph-wrapper {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--bg-secondary, #fff7e8);
  border: 2px solid var(--border-color, #2a220f);
}

.impact-graph-title {
  font-family: 'Press Start 2P', monospace;
  font-size: 9px;
  color: var(--color-accent, #26a8ff);
  margin: 0 0 12px 0;
}

.impact-graph-count {
  font-size: 8px;
  color: var(--color-text-dim, #b88230);
}

.impact-graph {
  position: relative;
  width: 100%;
  height: 360px;
}

.impact-graph__chart {
  width: 100%;
  height: 100%;
}

.impact-graph__warning {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 4px;
  font-size: 0.75rem;
}

.impact-graph-empty {
  padding: 24px;
  text-align: center;
  color: var(--color-text-dim, #b88230);
  font-family: 'Press Start 2P', monospace;
  font-size: 9px;
}
</style>
