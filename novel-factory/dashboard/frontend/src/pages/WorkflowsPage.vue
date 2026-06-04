<!--
  WorkflowsPage.vue — 工作流页面 (Phase 6.2 + 6.3)
  - 左侧:工作流列表 (含"查看图"按钮,Phase 6.3)
  - 右侧:启动表单 + 当前活跃状态 + 图渲染面板
-->
<template>
  <div class="workflows-page">
    <header class="page-header">
      <h1 class="page-title">工作流</h1>
      <div class="header-actions">
        <span
          class="ws-indicator pixel-border"
          :class="{ 'ws-indicator--on': wsConnected, 'ws-indicator--off': !wsConnected }"
          :title="wsError || (wsConnected ? '实时推送已连接' : '实时推送未连接')"
        >
          {{ wsConnected ? '● 实时' : '○ 离线' }}
        </span>
        <button class="refresh-btn pixel-border" @click="refresh" :disabled="loading">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div v-if="error" class="error-banner pixel-border">{{ error }}</div>

    <div class="workflows-layout">
      <!-- Left: workflow list -->
      <section class="wf-list-section">
        <h2 class="section-title">可用工作流 ({{ workflows.length }})</h2>
        <div v-if="loading && !workflows.length" class="loading">加载中…</div>
        <ul v-else class="wf-list">
          <li
            v-for="wf in workflows"
            :key="wf.name"
            class="wf-item"
            :class="{ 'wf-item--selected': selected?.name === wf.name }"
            @click="select(wf)"
          >
            <div class="wf-item-name">
              {{ wf.name }}
              <span v-if="wf.has_decision_nodes" class="badge decision-badge">
                有 DECISION
              </span>
            </div>
            <div class="wf-item-meta">
              <span class="meta-item">{{ wf.node_count }} 节点</span>
              <span class="meta-path">{{ wf.path }}</span>
            </div>
            <button
              v-if="selected?.name === wf.name"
              class="view-graph-btn pixel-border"
              :class="{ 'view-graph-btn--active': showGraph }"
              @click.stop="toggleGraph"
            >
              {{ showGraph ? '✕ 隐藏图' : '📊 查看图' }}
            </button>
          </li>
        </ul>
        <div v-if="!loading && !workflows.length" class="empty">
          未发现工作流 YAML
        </div>
      </section>

      <!-- Right: run form + status -->
      <section class="wf-run-section">
        <div v-if="selected" class="run-form pixel-card">
          <h2 class="section-title">运行: {{ selected.name }}</h2>
          <form @submit.prevent="runIt">
            <div class="form-group">
              <label class="form-label">初始输入 (JSON,可选)</label>
              <textarea
                v-model="initialInputsJson"
                class="form-textarea"
                rows="6"
                placeholder='{"chapter_num": 1, "characters": ["Lin Yun"]}'
              />
            </div>
            <div class="form-group">
              <label class="form-label">max_backtracks</label>
              <input
                v-model.number="maxBacktracks"
                type="number"
                min="0"
                max="10"
                class="form-input"
              />
            </div>
            <button type="submit" class="run-btn pixel-border" :disabled="running">
              {{ running ? '运行中…' : '🚀 启动' }}
            </button>
          </form>
        </div>

        <div v-else class="empty pixel-card">
          <p>请从左侧选择工作流</p>
        </div>

        <div v-if="active" class="active-status">
          <WorkflowStatus
            :status="active"
            @resume="handleResume"
          />
        </div>

        <div v-if="showGraph" class="graph-section">
          <WorkflowGraph
            v-if="graphData"
            :mermaid="graphData.mermaid"
            :workflow-name="graphData.workflow_name"
          />
          <div v-else-if="graphLoading" class="loading pixel-card">
            <p class="pixel-text">加载图中…</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import WorkflowStatus from '../components/WorkflowStatus.vue';
import WorkflowGraph from '../components/WorkflowGraph.vue';
import {
  fetchWorkflows,
  fetchWorkflowGraph,
  runWorkflow,
  resumeWorkflow,
} from '../api/index.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';

const workflows = ref([]);
const selected = ref(null);
const active = ref(null);
const initialInputsJson = ref('{}');
const maxBacktracks = ref(2);
const running = ref(false);
const loading = ref(false);
const error = ref(null);
const showGraph = ref(false);
const graphData = ref(null);
const graphLoading = ref(false);

// Phase 6.4: WebSocket 实时推送替代 2s 轮询
const {
  status: wsStatus,
  pendingDecisions: wsPending,
  connected: wsConnected,
  lastError: wsError,
} = useWorkflowSocket();

// 同步 WS 推送的 status → active
watch(wsStatus, (s) => {
  if (s) active.value = s;
}, { immediate: true });

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    workflows.value = await fetchWorkflows();
  } catch (e) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

function select(wf) {
  selected.value = wf;
  initialInputsJson.value = '{}';
  maxBacktracks.value = 2;
  // 切换工作流时清空图状态,避免显示旧的 mermaid
  showGraph.value = false;
  graphData.value = null;
}

async function runIt() {
  if (!selected.value) return;
  running.value = true;
  error.value = null;
  try {
    let initial_inputs = {};
    try {
      const parsed = JSON.parse(initialInputsJson.value || '{}');
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        initial_inputs = parsed;
      }
    } catch {
      throw new Error('初始输入 JSON 格式错误');
    }
    const result = await runWorkflow({
      workflow_name: selected.value.name,
      initial_inputs,
      max_backtracks: maxBacktracks.value,
    });
    // 立即更新一次 (不等 WS 推送)
    active.value = result;
  } catch (e) {
    error.value = `运行失败: ${e?.message || e}`;
  } finally {
    running.value = false;
  }
}

async function handleResume({ decisionId, option }) {
  try {
    const result = await resumeWorkflow(decisionId, option);
    // 立即更新,WS 也会推
    active.value = result;
  } catch (e) {
    error.value = `恢复失败: ${e?.message || e}`;
  }
}

async function toggleGraph() {
  showGraph.value = !showGraph.value;
  if (showGraph.value && selected.value && !graphData.value) {
    await loadGraph();
  }
}

async function loadGraph() {
  if (!selected.value) return;
  graphLoading.value = true;
  error.value = null;
  try {
    // Phase 6.6.D: includeStatus=true 触发后端叠加活跃工作流节点状态染色
    graphData.value = await fetchWorkflowGraph(selected.value.name, { includeStatus: true });
  } catch (e) {
    error.value = `加载图失败: ${e?.message || e}`;
  } finally {
    graphLoading.value = false;
  }
}

onMounted(refresh);
</script>

<style scoped>
.workflows-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.ws-indicator {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 4px 8px;
  background: var(--bg-secondary);
  color: var(--color-text-dim);
  border-width: 2px;
  cursor: default;
  user-select: none;
}

.ws-indicator--on {
  color: #4caf50;
  background: #e8f5e9;
}

.ws-indicator--off {
  color: #c62828;
  background: #ffebee;
}

.workflows-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--space-md);
  align-items: start;
}

@media (max-width: 768px) {
  .workflows-layout {
    grid-template-columns: 1fr;
  }
}

.section-title {
  font-size: 12px;
  font-family: 'Press Start 2P', monospace;
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-accent);
}

.wf-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.wf-item {
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  cursor: pointer;
  transition: all 0.1s;
}

.wf-item:hover {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 var(--border-color);
}

.wf-item--selected {
  background: var(--bg-primary);
  border-color: var(--color-accent);
}

.wf-item-name {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.badge {
  font-size: 6px;
  padding: 2px 4px;
  border: 1px solid var(--border-color);
}

.decision-badge {
  background: #fff59d;
  color: #000;
}

.wf-item-meta {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-xs);
  font-size: 8px;
  color: var(--color-text-dim);
}

.meta-path {
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60%;
}

.run-form {
  padding: var(--space-md);
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-bottom: var(--space-sm);
}

.form-label {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-text-dim);
}

.form-textarea,
.form-input {
  font-family: monospace;
  font-size: 11px;
  padding: var(--space-xs);
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  color: var(--color-text);
  resize: vertical;
}

.run-btn {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  padding: 10px 16px;
  background: var(--color-accent);
  color: var(--bg-primary);
  border: 2px solid var(--border-color);
  cursor: pointer;
  width: 100%;
}

.run-btn:hover:not(:disabled) {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 var(--border-color);
}

.run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty,
.loading {
  padding: var(--space-lg);
  text-align: center;
  color: var(--color-text-dim);
}

.error-banner {
  padding: var(--space-sm);
  background: #ffcdd2;
  color: #c62828;
  font-family: monospace;
  font-size: 11px;
}

.active-status {
  margin-top: var(--space-md);
}

.view-graph-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 4px 8px;
  margin-top: var(--space-xs);
  background: var(--bg-primary);
  color: var(--color-text);
  border: 2px solid var(--border-color);
  cursor: pointer;
}

.view-graph-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 2px 2px 0 var(--border-color);
}

.view-graph-btn--active {
  background: var(--color-accent);
  color: var(--bg-primary);
}

.graph-section {
  margin-top: var(--space-md);
}

.graph-section .loading {
  font-size: 10px;
  text-align: center;
  padding: var(--space-lg);
}
</style>
