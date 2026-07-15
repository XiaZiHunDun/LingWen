<!--
  CreatorAdvanceBatchPanel.vue — 脉络栏推进 batch / 生产引导（从 CreatorPage 拆出）
-->
<template>
  <div
    v-if="showAdvanceBatch && showAdvanceBatchOnCreator"
    class="advance-batch-panel pixel-border"
    data-testid="advance-batch-panel"
  >
    <h3 class="subsection-title">推进 batch</h3>
    <div class="batch-range">
      <label>
        起
        <input
          v-model.number="batchStart"
          type="number"
          min="1"
          class="vol-input vol-num"
          data-testid="batch-start-input"
        />
      </label>
      <label>
        止
        <input
          v-model.number="batchEnd"
          type="number"
          min="1"
          class="vol-input vol-num"
          data-testid="batch-end-input"
        />
      </label>
      <label>
        预算 $
        <input
          v-model.number="batchBudget"
          type="number"
          min="0"
          step="0.01"
          class="vol-input vol-num"
          data-testid="batch-budget-input"
        />
      </label>
    </div>
    <p
      v-if="uiProfile.batch_history_budget_hint && batchHistoryBudgetHint"
      class="meta-line batch-history-budget-hint"
      data-testid="batch-history-budget-hint"
    >
      {{ batchHistoryBudgetHint }}
    </p>
    <div class="batch-actions">
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="advance-preflight-btn"
        :disabled="batchRunning"
        @click="$emit('preflight')"
      >
        Preflight
      </button>
      <button
        type="button"
        class="save-btn pixel-border"
        data-testid="advance-batch-btn"
        :disabled="batchRunning || !preflightOk"
        @click="$emit('run-batch')"
      >
        {{ batchRunning ? '运行中…' : '启动 Batch' }}
      </button>
    </div>
    <p v-if="batchCommand" class="meta-line"><code>{{ batchCommand }}</code></p>
    <p v-if="batchError" class="batch-error">{{ batchError }}</p>
    <p v-if="batchJob" class="meta-line" data-testid="batch-job-status">
      任务 {{ batchJob.job_id }} · {{ batchJob.status }}
    </p>
  </div>

  <div
    v-else-if="showAdvanceBatch"
    class="advance-produce-cta pixel-border"
    data-testid="advance-produce-cta"
  >
    <h3 class="subsection-title">批量产章</h3>
    <p class="meta-line">
      Preflight、Batch 与生产记录已合并到「生产」页，避免与工作室重复操作。
    </p>
    <button
      type="button"
      class="save-btn pixel-border"
      data-testid="advance-go-produce-btn"
      @click="$emit('go-produce')"
    >
      去生产控制台
    </button>
  </div>
</template>

<script setup>
defineProps({
  showAdvanceBatch: { type: Boolean, required: true },
  showAdvanceBatchOnCreator: { type: Boolean, required: true },
  uiProfile: { type: Object, required: true },
  batchHistoryBudgetHint: { type: String, default: '' },
  batchRunning: { type: Boolean, required: true },
  preflightOk: { type: Boolean, required: true },
  batchCommand: { type: String, default: '' },
  batchError: { type: [String, Object], default: null },
  batchJob: { type: Object, default: null },
});

const batchStart = defineModel('batchStart', { type: Number, required: true });
const batchEnd = defineModel('batchEnd', { type: Number, required: true });
const batchBudget = defineModel('batchBudget', { type: Number, required: true });

defineEmits(['preflight', 'run-batch', 'go-produce']);
</script>

<style scoped>
.subsection-title {
  font-size: var(--text-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.advance-batch-panel {
  margin-top: var(--space-md);
  padding: var(--space-sm);
}

.advance-produce-cta {
  margin-top: var(--space-md);
  padding: var(--space-sm);
}

.batch-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--text-sm);
  margin-bottom: 6px;
}

.batch-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.batch-error {
  color: var(--color-danger);
  font-size: var(--text-sm);
  margin-top: 4px;
}

.batch-history-budget-hint {
  margin: var(--space-xs) 0 0;
  color: var(--color-accent);
}

.vol-input {
  font-size: var(--text-sm);
  padding: 2px 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
}

.vol-num {
  width: 3em;
}

.mini-btn,
.save-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}

.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}
</style>
