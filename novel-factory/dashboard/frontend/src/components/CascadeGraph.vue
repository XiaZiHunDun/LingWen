<!-- dashboard/frontend/src/components/CascadeGraph.vue (NEW, Phase 9.15 T3) -->
<!-- Lazy ECharts graph: cascade nodes (BFS 下游) + edges + node click emit.
  Cascade 子组件: 0 改 RippleDrawer 既有 audit timeline (T4 才接)
  dryRun mode 上色: trigger 绿 / modify 黄 / 其他 灰 -->
<template>
  <div
    v-if="cascade && cascade.cascade_nodes && cascade.cascade_nodes.length > 0"
    class="cascade-graph"
    data-testid="cascade-graph"
    :data-node-count="cascade.cascade_nodes.length"
  >
    <div ref="chartEl" class="cascade-graph__chart cascade-graph-chart" data-testid="cascade-graph-chart"></div>
    <div
      v-if="cascade.cascade_nodes.length > 100"
      class="cascade-graph__warning cascade-graph-warning"
      data-testid="cascade-graph-warning"
    >
      Truncated to first 100 nodes
    </div>
  </div>
  <div v-else class="cascade-graph-empty cascade-graph-empty-block" data-testid="cascade-graph-empty">
    No cascade yet
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue';

const props = defineProps({
  cascade: { type: Object, default: null },
  dryRun: { type: Boolean, default: false },
});
const emit = defineEmits(['nodeClick']);

const chartEl = ref(null);
let chart = null;

// Phase 9.15 dryRun 配色: 跟 RippleDrawer 既有 0 改, dryRun 子模式按 action 上色
function nodeColor(action) {
  if (props.dryRun) {
    if (action === 'trigger') return '#22c55e';
    if (action === 'modify') return '#eab308';
    return '#9ca3af';
  }
  return '#3b82f6';
}

async function initChart() {
  if (!chartEl.value || !props.cascade) return;
  // Lazy ECharts 加载 — 0 main bundle 增, 仅挂载时动态加载 graph series
  const echarts = await import('echarts/core');
  const { GraphChart } = await import('echarts/charts');
  const { TitleComponent, TooltipComponent } = await import('echarts/components');
  const { CanvasRenderer } = await import('echarts/renderers');
  echarts.use([GraphChart, TitleComponent, TooltipComponent, CanvasRenderer]);
  chart = echarts.init(chartEl.value);
  // 防御性: 100 节点上限, 超过显示 warning chip (UX 防 graph 爆炸)
  const nodes = (props.cascade.cascade_nodes || []).slice(0, 100).map((n) => ({
    id: n.id,
    name: `${n.id} (V${n.volume}c${n.chapter})`,
    symbolSize: 30,
    itemStyle: { color: nodeColor('trigger') },
  }));
  const edges = (props.cascade.cascade_edges || []).map((e) => ({
    source: e.from_node_id,
    target: e.to_node_id,
    lineStyle: { opacity: e.weight },
  }));
  chart.setOption({
    title: { text: `Cascade (depth ${props.cascade.depth_reached})`, left: 'center' },
    tooltip: {},
    series: [{ type: 'graph', layout: 'force', roam: true, data: nodes, edges, force: { repulsion: 100 } }],
  });
  // node click: emit { nodeId, volume, chapter } 让 parent drawer 跳章节 (T4 接)
  chart.on('click', (params) => {
    if (params.dataType === 'node') {
      const n = props.cascade.cascade_nodes.find((x) => x.id === params.data.id);
      if (n) emit('nodeClick', { nodeId: n.id, volume: n.volume, chapter: n.chapter });
    }
  });
}

onMounted(initChart);
onUnmounted(() => { if (chart) chart.dispose(); });
// cascade prop 变化时重新渲染 (loadCascade 完成 → 切换 → initChart 再跑)
watch(() => props.cascade, initChart);
</script>

<style scoped>
.cascade-graph { position: relative; width: 100%; height: 320px; }
.cascade-graph__chart { width: 100%; height: 100%; }
.cascade-graph__warning {
  position: absolute; top: 8px; right: 8px; padding: 4px 8px;
  background: #fef3c7; color: #92400e; border-radius: 4px; font-size: 0.8em;
}
.cascade-graph-empty { padding: 16px; color: #888; font-style: italic; text-align: center; }
</style>
