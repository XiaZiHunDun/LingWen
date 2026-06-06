<!--
  WorkflowStatus.vue — 工作流状态卡片 (Phase 6.2)
  显示运行/暂停/完成状态 + 节点统计 + pending decisions 列表
-->
<template>
  <div class="workflow-status pixel-card">
    <div class="status-header">
      <h3 class="status-title">
        {{ status.workflow_name || '未知工作流' }}
        <span class="status-pill" :class="statusClass">
          {{ statusLabel }}
        </span>
      </h3>
    </div>

    <div class="stat-grid">
      <div class="stat">
        <div class="stat-label">已完成</div>
        <div class="stat-value text-completed">{{ status.completed ?? 0 }}</div>
      </div>
      <div class="stat">
        <div class="stat-label">失败</div>
        <div class="stat-value text-failed">{{ status.failed ?? 0 }}</div>
      </div>
      <div class="stat">
        <div class="stat-label">总节点</div>
        <div class="stat-value">{{ status.node_count ?? 0 }}</div>
      </div>
      <div class="stat">
        <div class="stat-label">步数</div>
        <div class="stat-value">{{ status.steps ?? 0 }}</div>
      </div>
    </div>

    <div v-if="status.paused && status.paused_nodes?.length" class="paused-section">
      <h4 class="section-title">⏸ 暂停于节点</h4>
      <div class="paused-nodes">
        <span v-for="nid in status.paused_nodes" :key="nid" class="paused-node">
          {{ nid }}
        </span>
      </div>
    </div>

    <div v-if="status.pending_decisions?.length" class="pending-section">
      <h4 class="section-title">⚡ 待审核决策 ({{ status.pending_decisions.length }})</h4>
      <ul class="pending-list">
        <li v-for="d in status.pending_decisions" :key="d.decision_id" class="pending-item">
          <div class="pending-info">
            <span class="pending-kind">{{ d.kind }}</span>
            <span class="pending-node">{{ d.node_id }}</span>
            <span class="pending-priority">P{{ d.priority }}</span>
          </div>
          <p class="pending-prompt">{{ d.prompt }}</p>
          <div class="pending-actions">
            <button
              v-for="opt in (d.options || [])"
              :key="opt"
              class="resume-btn pixel-border"
              @click="onResume(d, opt)"
            >
              恢复 → {{ opt }}
            </button>
          </div>
        </li>
      </ul>
    </div>

    <ScoreRadarChart
      v-if="hasScores && firstScore"
      :scores-a="firstScore.scores_a || {}"
      :scores-b="firstScore.scores_b || {}"
      :label-a="firstScore.label_a || 'Variant A'"
      :label-b="firstScore.label_b || 'Variant B'"
      :winner="firstScore.winner || ''"
      :fallback="firstScore.fallback"
    />

    <div v-if="hasCost" class="cost-section">
      <h4 class="section-title">💰 Token 成本 (累计 USD)</h4>
      <p class="cost-total-usd">
        总计: ${{ totalCostText }}
      </p>
      <CostBarChart
        :cost-by-scenario="status.cost_by_scenario || {}"
        :cost-by-tier="status.cost_by_tier || {}"
        v-model:mode="costMode"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import ScoreRadarChart from './ScoreRadarChart.vue';
import CostBarChart from './CostBarChart.vue';

const props = defineProps({
  status: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['resume']);

// Phase 8.13: CostBarChart 切 mode (scenario | tier), v-model:mode 接
// default 'scenario' 保旧行为 (CostBarChart 也 default 'scenario' 兜底)
const costMode = ref('scenario');

const statusLabel = computed(() => {
  if (!props.status.is_active) return '未运行';
  if (props.status.paused) return '已暂停';
  return '运行中';
});

const statusClass = computed(() => {
  if (!props.status.is_active) return 'status-idle';
  if (props.status.paused) return 'status-paused';
  return 'status-running';
});

const scoreEntries = computed(() => {
  const data = props.status?.score_data || {};
  return Object.entries(data);
});
const firstScore = computed(() => scoreEntries.value[0]?.[1] || null);
const hasScores = computed(() => scoreEntries.value.length > 0);

const costByScenario = computed(() => props.status?.cost_by_scenario || {});
const hasCost = computed(() => {
  const data = costByScenario.value;
  return Object.keys(data).length > 0 && Object.values(data).some((v) => v > 0);
});
const totalCostText = computed(() => {
  const v = Number(props.status?.total_cost_usd ?? 0);
  return v.toFixed(4);
});

function onResume(decision, option) {
  emit('resume', { decisionId: decision.decision_id, option });
}
</script>

<style scoped>
.workflow-status {
  padding: var(--space-md);
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-title {
  font-size: 14px;
  font-family: 'Press Start 2P', monospace;
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.status-pill {
  font-size: 8px;
  padding: 4px 8px;
  border: 2px solid var(--border-color);
  font-family: 'Press Start 2P', monospace;
}

.status-idle { background: #cccccc; color: #000; }
.status-running { background: #c8e6c9; color: #000; }
.status-paused { background: #fff59d; color: #000; }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-sm);
}

.stat {
  padding: var(--space-sm);
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  text-align: center;
}

.stat-label {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-text-dim);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-family: 'Press Start 2P', monospace;
}

.text-completed { color: #388e3c; }
.text-failed { color: #c62828; }

.section-title {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  margin: 0 0 var(--space-xs) 0;
  color: var(--color-accent);
}

.paused-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.paused-node {
  font-size: 10px;
  font-family: monospace;
  padding: 4px 8px;
  background: #fff59d;
  border: 1px solid var(--border-color);
}

.pending-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.pending-item {
  padding: var(--space-sm);
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
}

.pending-info {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  font-size: 8px;
  font-family: monospace;
  margin-bottom: 4px;
}

.pending-kind {
  background: var(--color-accent);
  color: var(--bg-primary);
  padding: 2px 6px;
}

.pending-node {
  color: var(--color-text-dim);
}

.pending-priority {
  margin-left: auto;
  color: var(--color-accent);
  font-weight: bold;
}

.pending-prompt {
  font-size: 11px;
  margin: 4px 0;
  line-height: 1.4;
}

.pending-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.resume-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 6px 10px;
  background: #c8e6c9;
  border: 2px solid var(--border-color);
  cursor: pointer;
}

.resume-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 2px 2px 0 var(--border-color);
}

.cost-section {
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.cost-total-usd {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-accent);
  margin: 0;
}
</style>
