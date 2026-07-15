<!-- dashboard/frontend/src/components/CascadeGraph.vue (NEW, Phase 9.15 T3) -->
<!-- Lazy ECharts graph: cascade nodes (BFS 下游) + edges + node click emit.
  Phase 9.51 F40: 3 view modes — force | depth-layer | action-cluster -->
<template>
  <div
    v-if="cascade && cascade.cascade_nodes && cascade.cascade_nodes.length > 0"
    class="cascade-graph"
    data-testid="cascade-graph"
    :data-node-count="cascade.cascade_nodes.length"
    :data-view-mode="viewMode"
  >
    <div
      class="cascade-graph__toolbar"
      data-testid="cascade-view-toggle"
      role="tablist"
      aria-label="Cascade graph view mode"
    >
      <button
        v-for="mode in viewModes"
        :key="mode"
        type="button"
        role="tab"
        :class="['cascade-view-tab', { active: viewMode === mode }]"
        :aria-selected="viewMode === mode"
        :data-testid="`cascade-view-${mode}`"
        @click="viewMode = mode"
      >
        {{ viewModeLabels[mode] }}
      </button>
    </div>
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
import {
  CASCADE_VIEW_MODES,
  CASCADE_VIEW_MODE_LABELS,
  buildCascadeChartOption,
  actionNodeColor,
} from '../utils/cascadeGraphUtils.js';

const props = defineProps({
  cascade: { type: Object, default: null },
  dryRun: { type: Boolean, default: false },
});
const emit = defineEmits(['nodeClick']);

const viewModes = CASCADE_VIEW_MODES;
const viewModeLabels = CASCADE_VIEW_MODE_LABELS;
const viewMode = ref('force');

const chartEl = ref(null);
let chart = null;

// Backward-compat export for tests (Phase 9.15 dryRun palette)
function nodeColor(action) {
  return actionNodeColor(action, props.dryRun);
}

defineExpose({ nodeColor });

async function initChart() {
  if (!chartEl.value || !props.cascade) return;
  const echarts = await import('echarts/core');
  const { GraphChart } = await import('echarts/charts');
  const { TitleComponent, TooltipComponent } = await import('echarts/components');
  const { CanvasRenderer } = await import('echarts/renderers');
  echarts.use([GraphChart, TitleComponent, TooltipComponent, CanvasRenderer]);
  if (!chart) {
    chart = echarts.init(chartEl.value);
    chart.on('click', (params) => {
      if (params.dataType === 'node') {
        const n = props.cascade.cascade_nodes.find((x) => x.id === params.data.id);
        if (n) emit('nodeClick', { nodeId: n.id, volume: n.volume, chapter: n.chapter });
      }
    });
  }
  chart.setOption(buildCascadeChartOption(props.cascade, viewMode.value, props.dryRun), true);
}

onMounted(initChart);
onUnmounted(() => { if (chart) chart.dispose(); });
watch(() => [props.cascade, props.dryRun, viewMode.value], initChart);
</script>

<style scoped>
.cascade-graph { position: relative; width: 100%; height: 360px; display: flex; flex-direction: column; }
.cascade-graph__toolbar {
  display: flex; gap: 4px; padding: 4px 0 8px 0;
}
.cascade-view-tab {
  padding: 4px 10px; border: 1px solid #cbd5e1; background: #fff; border-radius: 4px;
  font-size: 0.75em; cursor: pointer; color: #475569;
}
.cascade-view-tab:hover { border-color: #3b82f6; color: #1e40af; }
.cascade-view-tab.active {
  background: #eff6ff; border-color: #3b82f6; color: #1e40af; font-weight: 600;
}
.cascade-graph__chart { flex: 1; width: 100%; min-height: 280px; }
.cascade-graph__warning {
  position: absolute; top: 40px; right: 8px; padding: 4px 8px;
  background: #fef3c7; color: #92400e; border-radius: 4px; font-size: 0.8em;
}
.cascade-graph-empty { padding: 16px; color: #888; font-style: italic; text-align: center; }
</style>
