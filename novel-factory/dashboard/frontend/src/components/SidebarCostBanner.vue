<!--
  SidebarCostBanner.vue — Sidebar 底部持续 cost banner (Phase 8.11 + 8.11 fixup + 8.12 + 8.15)
  显示 total USD + budget line + progress bar。
  有 cost_by_scenario entry 才显示 (空状态隐藏避免占 vertical space)。
  跨 4 page (Overview / Decisions / Workflows / placeholders) 持续可见。
  Phase 8.12: 3 档 budget (per-run/per-day/per-week) priority cascade — 显最紧急档
  (exceeded 优先, 同状态按 used_pct desc), 含 label 本次/今日/本周。
  Phase 8.15: 加 3 个 per-tier budget row (haiku/sonnet/opus) 在 activeBudget 进度条下方
  (跟 Phase 8.12 cascade 不冲突, 4 块: total + active + 3 tier rows). 顺序 Enum
  顺序 (haiku → sonnet → opus, deterministic). 未设 tier 跳过 (filter entry 为空 dict).
-->
<template>
  <div
    v-if="hasCost"
    class="sidebar-cost-banner"
    role="region"
    aria-label="成本追踪"
  >
    <!-- Phase 8.16 NEW: 顶部 segmented control (在 total 之前) -->
    <div class="time-window-tabs" role="tablist" aria-label="成本时间窗口">
      <button
        v-for="opt in TIME_OPTIONS"
        :key="opt.value"
        :class="['time-window-tab', { active: timeWindow === opt.value }]"
        :data-testid="`sidebar-time-window-${opt.value}`"
        role="tab"
        :aria-selected="timeWindow === opt.value"
        @click="setTimeWindow(opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>
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
    <!-- Phase 8.15 NEW: per-tier budget rows (haiku/sonnet/opus) -->
    <template v-for="tier in tierBudgets" :key="tier.name">
      <div data-testid="sidebar-cost-tier-row">
        <div
          class="sidebar-cost-row sidebar-cost-tier-row"
          role="status"
          aria-live="polite"
        >
          <span class="sidebar-cost-tier-text">
            {{ tier.label }} 预算: ${{ tier.used }} / ${{ tier.budget }} ({{ tier.pct }}%)
          </span>
        </div>
        <div
          class="progress-bar"
          role="progressbar"
          :aria-valuenow="Math.round(parseFloat(tier.pct))"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-label="`${tier.label} 预算状态: 已用 ${tier.used} 美元 / 预算 ${tier.budget} 美元 (${tier.pct}%)`"
        >
          <div
            class="progress-bar-fill"
            :class="tier.status === 'exceeded' ? 'exceeded' : 'ok'"
            :style="{ width: tier.pct + '%' }"
          ></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useCostWindow } from '../composables/useCostWindow.js';  // Phase 8.16
import { TIME_OPTIONS } from '../composables/useTimeOptions.js';  // Phase 8.20

const props = defineProps({
  status: {
    type: Object,
    required: true,
  },
});

// Phase 8.16: time window composable (跟 WorkflowStatus 共享 singleton)
const { timeWindow, windowedCost, setTimeWindow } = useCostWindow();

// display* 模式同 WorkflowStatus
const displayCostByScenario = computed(() =>
  windowedCost.value?.cost_by_scenario ?? props.status?.cost_by_scenario ?? {}
);
const displayCostByTier = computed(() =>
  windowedCost.value?.cost_by_tier ?? props.status?.cost_by_tier ?? {}
);
const displayTotalCost = computed(() =>
  windowedCost.value?.total_cost_usd ?? props.status?.total_cost_usd ?? 0.0
);

// Phase 8.17: hasCost OR scenario + tier (symmetric to Phase 8.14 WorkflowStatus fix)
// — 防止 tier-only 数据时整 banner 隐藏. display* 走 windowedCost 路径优先
// (windowedCost 7d/30d 时 → time window 路径; null 时 → WS 全量 fallback).
const costByScenario = computed(() => displayCostByScenario.value);
const costByTier = computed(() => displayCostByTier.value);
const hasCost = computed(() => {
  const scenarioHas = Object.keys(costByScenario.value).length > 0
    && Object.values(costByScenario.value).some((v) => v > 0);
  const tierHas = Object.keys(costByTier.value).length > 0
    && Object.values(costByTier.value).some((v) => v > 0);
  return scenarioHas || tierHas;
});

const totalUsd = computed(() => Number(displayTotalCost.value ?? 0));
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

// Phase 8.15 NEW: per-tier budget rows (haiku/sonnet/opus, 顺序 Enum 顺序)
// 跟 Phase 8.12 activeBudget cascade 不冲突 — 加 row 不动 cascade
// 未设 tier (空 dict) → 跳过 (filter out)
// 顺序 hardcode: haiku → sonnet → opus (跟 ModelTier 枚举顺序一致, deterministic)
const TIER_ORDER = ['haiku', 'sonnet', 'opus'];
const tierBudgets = computed(() => {
  const data = props.status?.budget_by_tier || {};
  const list = [];
  for (const tierName of TIER_ORDER) {
    const entry = data[tierName];
    if (!entry || entry.budget_usd == null) continue;  // 未设跳过
    const used = Number(entry.used_usd ?? 0);
    const budget = Number(entry.budget_usd ?? 0);
    const pct = budget > 0 ? (used / budget) * 100 : 0;
    list.push({
      name: tierName,
      label: tierName,  // 3 tier 用 lowercase key (跟 Phase 8.13 CostBarChart mode toggle 一致)
      used: used.toFixed(4),
      budget: budget.toFixed(4),
      pct: Math.max(0, Math.min(100, pct)).toFixed(1),  // 0-100 范围 clamp
      status: entry.status || 'ok',
    });
  }
  return list;
});
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

/* Phase 8.15 NEW: per-tier budget row (跟 .sidebar-cost-row 同 layout,
   独立 class for data-testid selector). 0 改 .sidebar-cost-row 旧 layout. */
.sidebar-cost-tier-row {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 8px;
  line-height: 1.5;
}

.sidebar-cost-tier-text {
  flex: 1;
  color: var(--color-text-dim);
}

/* Phase 8.16 NEW: .time-window-tabs 跟 .time-window-tab (跟 WorkflowStatus 同 pattern,
   scoped CSS 不冲突 — 独立 component). */
.time-window-tabs {
  display: flex;
  gap: var(--space-xs);
}
.time-window-tab {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 4px 8px;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  cursor: pointer;
}
.time-window-tab:hover { transform: translate(-1px, -1px); }
.time-window-tab.active {
  background: var(--color-accent);
  color: var(--bg-primary);
}
</style>
