<!--
  DecisionCard.vue — 单个决策卡片
  Phase 6.2: 显示 kind badge + prompt + options (按钮组) + resolve/defer/cancel
  Phase 6.6.B: + status badge (✅⏸❌) + meta info (解决人/选项/时间/原因) + resolve 守卫
-->
<template>
  <div class="decision-card pixel-card">
    <div class="card-header">
      <span class="kind-badge" :class="`kind-${kindClass}`">{{ kindLabel }}</span>
      <span class="priority-badge" v-if="decision.priority !== undefined">
        P{{ decision.priority }}
      </span>
      <span
        v-if="statusBadge"
        class="status-badge"
        :class="statusBadge.cls"
      >{{ statusBadge.label }}</span>
      <span class="node-id">{{ decision.node_id }}</span>
    </div>

    <p class="prompt">{{ decision.prompt }}</p>

    <div v-if="decision.context && Object.keys(decision.context).length" class="context">
      <details>
        <summary>上下文</summary>
        <pre>{{ JSON.stringify(decision.context, null, 2) }}</pre>
      </details>
    </div>

    <div v-if="decision.status === 'pending'" class="options">
      <button
        v-for="opt in decision.options || []"
        :key="opt"
        class="option-btn pixel-border"
        :disabled="busy"
        @click="onResolve(opt)"
      >
        {{ opt }}
      </button>
    </div>

    <div v-if="decision.status === 'pending'" class="actions">
      <button
        class="action-btn defer-btn pixel-border"
        :disabled="busy"
        @click="onDefer"
      >
        推迟
      </button>
      <button
        class="action-btn cancel-btn pixel-border"
        :disabled="busy"
        @click="onCancel"
      >
        取消
      </button>
    </div>

    <div v-else class="actions actions-readonly">
      <span class="readonly-hint">🔒 此决策已{{
        decision.status === 'resolved' ? '解决' : decision.status === 'cancelled' ? '取消' : '推迟'
      }}</span>
    </div>

    <div v-if="metaInfo" class="meta-info">
      {{ metaInfo }}
    </div>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  decision: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['resolve', 'defer', 'cancel']);

const busy = ref(false);
const error = ref(null);

const kindLabel = computed(() => {
  const map = {
    outline_judgment: '大纲审核',
    volume_judgment: '卷审核',
    chapter_iteration_judgment: '章节迭代',
    publish_judgment: '发布审核',
    subplot_open: '支线开启',
    subplot_close: '支线收束',
    style_pick: '风格选择',
  };
  return map[props.decision.kind] || props.decision.kind || '决策';
});

const kindClass = computed(() => {
  return (props.decision.kind || 'unknown').replace(/_/g, '-');
});

// Phase 6.6.B: status badge (resolved/deferred/cancelled 才有, pending 不显示)
const statusBadge = computed(() => {
  const map = {
    resolved: { label: '✅ 已解决', cls: 'status-resolved' },
    deferred: { label: '⏸ 已推迟', cls: 'status-deferred' },
    cancelled: { label: '❌ 已取消', cls: 'status-cancelled' },
  };
  return map[props.decision.status] || null;
});

// Phase 6.6.B: meta info (解决人/选项/时间/原因)
const metaInfo = computed(() => {
  const d = props.decision;
  if (d.status === 'pending') return null;
  const parts = [];
  if (d.resolved_by) parts.push(`解决人: ${d.resolved_by}`);
  if (d.resolution) parts.push(`选项: ${d.resolution}`);
  if (d.resolved_at) {
    const dt = new Date(d.resolved_at);
    parts.push(`时间: ${dt.toLocaleString('zh-CN', { hour12: false })}`);
  }
  if (d.reason) {
    const verb = d.status === 'cancelled' ? '取消' : '推迟';
    parts.push(`${verb}原因: ${d.reason}`);
  }
  return parts.join(' · ');
});

async function onResolve(option) {
  busy.value = true;
  error.value = null;
  try {
    emit('resolve', { decisionId: props.decision.decision_id, option });
  } finally {
    busy.value = false;
  }
}

async function onDefer() {
  busy.value = true;
  error.value = null;
  try {
    const reason = window.prompt('推迟原因 (可选):', '') || '';
    emit('defer', { decisionId: props.decision.decision_id, reason });
  } finally {
    busy.value = false;
  }
}

async function onCancel() {
  if (!window.confirm('确定取消此决策?此操作不可撤销。')) return;
  busy.value = true;
  error.value = null;
  try {
    const reason = window.prompt('取消原因 (可选):', '') || '';
    emit('cancel', { decisionId: props.decision.decision_id, reason });
  } finally {
    busy.value = false;
  }
}
</script>

<style scoped>
.decision-card {
  padding: var(--space-md);
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.kind-badge {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 4px 8px;
  border: 2px solid var(--border-color);
}

.kind-outline-judgment { background: #fff59d; color: #000; }
.kind-volume-judgment { background: #c8e6c9; color: #000; }
.kind-chapter-iteration-judgment { background: #bbdefb; color: #000; }
.kind-publish-judgment { background: #ffcdd2; color: #000; }
.kind-subplot-open { background: #e1bee7; color: #000; }
.kind-subplot-close { background: #d1c4e9; color: #000; }
.kind-style-pick { background: #ffe0b2; color: #000; }

.priority-badge {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-accent);
}

.node-id {
  font-size: 8px;
  color: var(--color-text-dim);
  margin-left: auto;
}

.prompt {
  font-size: 12px;
  color: var(--color-text);
  line-height: 1.5;
  margin: 0;
}

.context summary {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  cursor: pointer;
  color: var(--color-text-dim);
}

.context pre {
  font-size: 10px;
  background: var(--bg-primary);
  padding: var(--space-xs);
  overflow-x: auto;
}

.options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.option-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 8px 12px;
  background: var(--color-accent);
  color: var(--bg-primary);
  border: 2px solid var(--border-color);
  cursor: pointer;
  transition: transform 0.1s;
}

.option-btn:hover:not(:disabled) {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 var(--border-color);
}

.option-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.actions {
  display: flex;
  gap: var(--space-sm);
  border-top: 1px dashed var(--border-color);
  padding-top: var(--space-sm);
}

.action-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 6px 10px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  cursor: pointer;
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-secondary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-text {
  font-size: 10px;
  color: #c62828;
  font-family: monospace;
}

/* Phase 6.6.B: status badge (resolved/deferred/cancelled 颜色) */
.status-badge {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 3px 6px;
  border: 2px solid;
  margin-left: var(--space-xs);
}

.status-resolved {
  color: #2e7d32;
  border-color: #2e7d32;
  background: #c8e6c9;
}

.status-deferred {
  color: #f57c00;
  border-color: #f57c00;
  background: #ffe0b2;
}

.status-cancelled {
  color: #616161;
  border-color: #616161;
  background: #e0e0e0;
}

.meta-info {
  font-size: 9px;
  font-family: monospace;
  color: var(--color-text-dim);
  background: var(--bg-primary);
  border-left: 3px solid var(--color-accent);
  padding: var(--space-xs) var(--space-sm);
  margin-top: var(--space-sm);
  word-break: break-all;
}

.actions-readonly {
  opacity: 0.6;
}

.readonly-hint {
  font-size: 9px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-text-dim);
}
</style>
