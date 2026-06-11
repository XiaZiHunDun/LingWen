<!--
  SidebarTierBudgetAlerts.vue — Sidebar tier budget alert log (Phase 9.27 F11)
  顶部 alert 列表, 记录超阈值 tier + 时间戳 (warning >=80% / exceeded >=100%).
-->
<template>
  <section
    v-if="alerts.length > 0"
    class="sidebar-tier-budget-alerts"
    data-testid="sidebar-tier-budget-alerts"
    role="log"
    aria-label="Tier 预算告警"
  >
    <div class="sidebar-tier-budget-alerts-title">预算告警</div>
    <ul class="sidebar-tier-budget-alerts-list">
      <li
        v-for="alert in alerts"
        :key="alert.id"
        class="sidebar-tier-budget-alert-item"
        :class="`sidebar-tier-budget-alert-${alert.level}`"
        :data-testid="`sidebar-tier-budget-alert-${alert.tier}`"
        role="listitem"
      >
        <span class="sidebar-tier-budget-alert-icon">
          {{ alert.level === 'exceeded' ? '🚨' : '⚠️' }}
        </span>
        <span class="sidebar-tier-budget-alert-text">
          {{ alert.tier }}
          {{ alert.level === 'exceeded' ? '超预算' : '接近上限' }}
          {{ alert.pct }}%
          ({{ timeWindowLabel(alert.timeWindow) }})
        </span>
        <time
          class="sidebar-tier-budget-alert-time"
          :datetime="alert.timestamp"
          :data-testid="`sidebar-tier-budget-alert-time-${alert.tier}`"
        >
          {{ formatAlertTime(alert.timestamp) }}
        </time>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { watch } from 'vue';
import { useCostWindow } from '../composables/useCostWindow.js';
import {
  useTierBudgetAlerts,
} from '../composables/useTierBudgetAlerts.js';

const props = defineProps({
  status: {
    type: Object,
    required: true,
  },
});

const { timeWindow, windowedCost } = useCostWindow();
const {
  alerts,
  syncTierBudgetAlerts,
  computeTierBudgetState,
  formatAlertTime,
  timeWindowLabel,
} = useTierBudgetAlerts();

watch(
  () => [
    props.status?.budget_by_tier,
    timeWindow.value,
    windowedCost.value?.cost_by_tier,
  ],
  () => {
    const states = computeTierBudgetState({
      budgetByTier: props.status?.budget_by_tier ?? {},
      timeWindow: timeWindow.value,
      windowedCostByTier: windowedCost.value?.cost_by_tier ?? null,
    });
    syncTierBudgetAlerts(states, timeWindow.value);
  },
  { deep: true, immediate: true },
);
</script>

<style scoped>
.sidebar-tier-budget-alerts {
  padding: var(--space-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  font-family: 'Press Start 2P', monospace;
}

.sidebar-tier-budget-alerts-title {
  font-size: 7px;
  color: var(--color-text-dim);
  margin-bottom: 6px;
  text-align: center;
}

.sidebar-tier-budget-alerts-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-tier-budget-alert-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  font-size: 6px;
  line-height: 1.4;
  padding: 3px 4px;
  border-radius: 2px;
}

.sidebar-tier-budget-alert-warning {
  background: #fff8e1;
  color: #856404;
  border: 1px solid #ffc107;
}

.sidebar-tier-budget-alert-exceeded {
  background: #fdecea;
  color: #c0392b;
  border: 1px solid #f56c6c;
}

.sidebar-tier-budget-alert-icon {
  font-family: 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif;
  font-size: 8px;
}

.sidebar-tier-budget-alert-text {
  flex: 1;
}

.sidebar-tier-budget-alert-time {
  font-size: 6px;
  color: var(--color-text-dim);
}
</style>
