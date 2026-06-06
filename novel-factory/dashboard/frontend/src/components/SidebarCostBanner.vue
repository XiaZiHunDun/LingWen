<!--
  SidebarCostBanner.vue — Sidebar 底部持续 cost banner (Phase 8.11 + 8.11 fixup + 8.12)
  显示 total USD + budget line + progress bar。
  有 cost_by_scenario entry 才显示 (空状态隐藏避免占 vertical space)。
  跨 4 page (Overview / Decisions / Workflows / placeholders) 持续可见。
  Phase 8.12: 3 档 budget (per-run/per-day/per-week) priority cascade — 显最紧急档
  (exceeded 优先, 同状态按 used_pct desc), 含 label 本次/今日/本周。
-->
<template>
  <div
    v-if="hasCost"
    class="sidebar-cost-banner"
    role="region"
    aria-label="成本追踪"
  >
    <div class="sidebar-cost-row" role="status" aria-live="polite">
      <span class="sidebar-cost-total-text">
        <span class="sidebar-cost-icon">💰</span>${{ totalText }}
      </span>
    </div>
    <div
      v-if="activeBudget"
      class="sidebar-cost-row"
      role="status"
      aria-live="polite"
    >
      <span class="sidebar-cost-budget-text">
        {{ activeBudget.label }}预算: ${{ activeUsedText }} / ${{ activeBudgetText }} ({{ activePctText }}%)
      </span>
    </div>
    <div
      v-if="activeBudget"
      class="progress-bar"
      role="progressbar"
      :aria-valuenow="Math.round(activePct)"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="`${activeBudget.label}预算状态: 已用 ${activeUsedText} 美元 / 预算 ${activeBudgetText} 美元 (${activePctText}%)`"
    >
      <div
        class="progress-bar-fill"
        :class="activeBudget.status === 'exceeded' ? 'exceeded' : 'ok'"
        :style="{ width: activePct + '%' }"
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

// Phase 8.12 NEW: 3 档 budget 收集 + label
// 收 3 档 budget (per-run/per-day/per-week), 每档加 label (本次/今日/本周)
// 旧 1 档 (per-run cost_budget_status) 保留兼容, 通过 list 合并入 allBudgets
const allBudgets = computed(() => {
  const list = [];
  const perRun = props.status?.cost_budget_status;
  if (perRun && perRun.budget_usd != null) {
    list.push({ ...perRun, scope: 'run', label: '本次' });
  }
  const perDay = props.status?.budget_per_day;
  if (perDay && perDay.budget_usd != null) {
    list.push({ ...perDay, scope: 'day', label: '今日' });
  }
  const perWeek = props.status?.budget_per_week;
  if (perWeek && perWeek.budget_usd != null) {
    list.push({ ...perWeek, scope: 'week', label: '本周' });
  }
  return list;
});

// Phase 8.12 NEW: priority cascade — exceeded 优先, 同状态按 used_pct desc
// 例如 per-run 50% ok + per-day 120% exceeded + per-week 80% ok → 返 per-day
// 旧 hasBudget 单一 budget 块 → activeBudget 替代 (list 长度 0 时 activeBudget = null)
const activeBudget = computed(() => {
  if (allBudgets.value.length === 0) return null;
  return [...allBudgets.value].sort((a, b) => {
    if (a.status === 'exceeded' && b.status !== 'exceeded') return -1;
    if (b.status === 'exceeded' && a.status !== 'exceeded') return 1;
    return b.used_pct - a.used_pct;
  })[0];
});

const activePct = computed(() => {
  if (!activeBudget.value) return 0;
  return Math.max(0, Math.min(100, Number(activeBudget.value.used_pct ?? 0)));
});
const activeUsedText = computed(() =>
  activeBudget.value ? Number(activeBudget.value.used_usd ?? 0).toFixed(4) : '0.0000'
);
const activeBudgetText = computed(() =>
  activeBudget.value ? Number(activeBudget.value.budget_usd ?? 0).toFixed(4) : '0.0000'
);
const activePctText = computed(() => activePct.value.toFixed(1));
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
