<!--
  SidebarCostBanner.vue — Sidebar 底部持续 cost banner (Phase 8.11)
  显示 total USD + budget line + progress bar。
  有 cost_by_scenario entry 才显示 (空状态隐藏避免占 vertical space)。
  跨 4 page (Overview / Decisions / Workflows / placeholders) 持续可见。
-->
<template>
  <div v-if="hasCost" class="sidebar-cost-banner">
    <div class="sidebar-cost-row">
      <span class="sidebar-cost-total-text">
        <span class="sidebar-cost-icon">💰</span>${{ totalText }}
      </span>
    </div>
    <div v-if="hasBudget" class="sidebar-cost-row">
      <span class="sidebar-cost-budget-text">
        预算: ${{ usedText }} / ${{ budgetText }} ({{ pctText }}%)
      </span>
    </div>
    <div v-if="hasBudget" class="progress-bar">
      <div
        class="progress-bar-fill"
        :class="budgetClass"
        :style="{ width: pct + '%' }"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  status: {
    type: Object,
    required: true,
  },
});

const costByScenario = computed(() => props.status?.cost_by_scenario || {});
const hasCost = computed(() => {
  const data = costByScenario.value;
  return Object.keys(data).length > 0 && Object.values(data).some((v) => v > 0);
});

const totalUsd = computed(() => Number(props.status?.total_cost_usd ?? 0));
const totalText = computed(() => totalUsd.value.toFixed(4));

const budget = computed(() => props.status?.cost_budget_status || {});
const hasBudget = computed(() => budget.value && budget.value.budget_usd != null);
const usedText = computed(() => (budget.value.used_usd == null ? '0.0000' : Number(budget.value.used_usd).toFixed(4)));
const budgetText = computed(() => (budget.value.budget_usd == null ? '0.0000' : Number(budget.value.budget_usd).toFixed(4)));
const pct = computed(() => {
  const p = Number(budget.value.used_pct ?? 0);
  return Math.max(0, Math.min(100, p));
});
const pctText = computed(() => pct.value.toFixed(1));
const budgetClass = computed(() => (budget.value.status === 'exceeded' ? 'exceeded' : 'ok'));
</script>

<style scoped>
.sidebar-cost-banner {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  border-top: 2px solid var(--border-color);
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-family: 'Press Start 2P', monospace;
}

.sidebar-cost-row {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 8px;
  line-height: 1.5;
}

.sidebar-cost-icon {
  font-size: 10px;
  font-family: 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif;
  margin-right: 4px;
}

.sidebar-cost-total-text {
  flex: 1;
  color: var(--color-accent);
}

.sidebar-cost-budget-text {
  flex: 1;
  color: var(--color-text-dim);
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #e0e0e0;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  transition: width 0.2s ease-out;
}

.progress-bar-fill.ok {
  background: var(--color-success);
}

.progress-bar-fill.exceeded {
  background: #f56c6c;
}
</style>
