<!--
  WorkflowGraph.vue — 渲染 mermaid 工作流图 (Phase 6.3)
  接受 mermaid 字符串 + 可选 workflow_name,异步渲染为 SVG
-->
<template>
  <div class="workflow-graph">
    <div v-if="loading" class="loading-state pixel-card">
      <p class="pixel-text">渲染图中…</p>
    </div>

    <div v-else-if="error" class="error-state pixel-card">
      <p class="error-title">⚠ 渲染失败</p>
      <pre class="error-detail">{{ error }}</pre>
    </div>

    <div v-else-if="svg" class="graph-container pixel-card">
      <div class="graph-header">
        <span class="graph-title">{{ workflowName || '工作流图' }}</span>
        <button class="reset-zoom-btn pixel-border" @click="resetZoom">⤢ 重置缩放</button>
      </div>
      <div
        ref="containerRef"
        class="svg-wrapper"
        :style="{ transform: `scale(${zoom})` }"
        v-html="svg"
      />
    </div>

    <div v-else class="empty-state pixel-card">
      <p class="pixel-text">未提供 mermaid 字符串</p>
    </div>

    <div v-if="svg" class="zoom-controls">
      <button class="zoom-btn pixel-border" @click="zoomIn" :disabled="zoom >= 2">＋</button>
      <span class="zoom-display">{{ (zoom * 100).toFixed(0) }}%</span>
      <button class="zoom-btn pixel-border" @click="zoomOut" :disabled="zoom <= 0.4">－</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import mermaid from 'mermaid';

const props = defineProps({
  mermaid: { type: String, default: '' },
  workflowName: { type: String, default: '' },
});

const loading = ref(false);
const error = ref(null);
const svg = ref(null);
const zoom = ref(1);
const containerRef = ref(null);
let renderId = 0;

// 初始化 mermaid (一次性)
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: '"Press Start 2P", monospace',
  flowchart: {
    useMaxWidth: true,
    htmlLabels: true,
    curve: 'basis',
  },
});

async function render() {
  if (!props.mermaid) {
    svg.value = null;
    return;
  }
  loading.value = true;
  error.value = null;
  renderId += 1;
  const myId = renderId;
  try {
    // mermaid.render() 期望唯一 ID
    const id = `mermaid-${myId}-${Date.now()}`;
    const { svg: svgStr } = await mermaid.render(id, props.mermaid);
    if (myId === renderId) {
      svg.value = svgStr;
    }
  } catch (e) {
    if (myId === renderId) {
      error.value = e?.message || String(e);
    }
  } finally {
    if (myId === renderId) {
      loading.value = false;
    }
  }
}

function zoomIn() {
  zoom.value = Math.min(2, zoom.value + 0.2);
}

function zoomOut() {
  zoom.value = Math.max(0.4, zoom.value - 0.2);
}

function resetZoom() {
  zoom.value = 1;
}

watch(
  () => props.mermaid,
  () => {
    nextTick(render);
  },
);

onMounted(render);
onBeforeUnmount(() => {
  renderId += 1;  // 取消 in-flight
});
</script>

<style scoped>
.workflow-graph {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  position: relative;
}

.graph-container,
.loading-state,
.error-state,
.empty-state {
  padding: var(--space-md);
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 2px dashed var(--border-color);
}

.graph-title {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-accent);
}

.reset-zoom-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 4px 8px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  cursor: pointer;
}

.svg-wrapper {
  overflow: auto;
  text-align: center;
  transform-origin: top center;
  transition: transform 0.2s;
  max-height: 70vh;
  padding: var(--space-sm);
  background: white;  /* mermaid 默认白底,便于配色 */
}

.svg-wrapper :deep(svg) {
  max-width: 100%;
  height: auto;
}

.zoom-controls {
  position: sticky;
  bottom: var(--space-sm);
  display: flex;
  gap: var(--space-xs);
  align-items: center;
  justify-content: center;
  padding: var(--space-xs);
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  align-self: center;
}

.zoom-btn {
  font-size: 12px;
  font-family: monospace;
  width: 32px;
  height: 32px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  cursor: pointer;
}

.zoom-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.zoom-display {
  font-size: 10px;
  font-family: monospace;
  min-width: 50px;
  text-align: center;
}

.error-state .error-title {
  color: #c62828;
  font-size: 12px;
  font-family: 'Press Start 2P', monospace;
  margin: 0 0 var(--space-sm) 0;
}

.error-state .error-detail {
  font-size: 10px;
  font-family: monospace;
  white-space: pre-wrap;
  background: var(--bg-primary);
  padding: var(--space-sm);
  max-height: 200px;
  overflow: auto;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-dim);
}
</style>
