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
  border: var(--border-width) solid #e8c468;
  border-radius: var(--radius-sm);
  background: #fffaf0;
  font-family: var(--font-ui);
}

.sidebar-tier-budget-alerts-title {
  font-size: var(--text-xs);
  font-weight: 700;
  color: #7a4b00;
  margin-bottom: var(--space-xs);
}

.sidebar-tier-budget-alerts-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sidebar-tier-budget-alert-item {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 6px;
  font-size: var(--text-xs);
  line-height: 1.45;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
}

.sidebar-tier-budget-alert-warning {
  background: #fff8e8;
  color: #5c3d00;
  border: var(--border-width) solid #e8c468;
}

.sidebar-tier-budget-alert-exceeded {
  background: #fef2f2;
  color: #7f1d1d;
  border: var(--border-width) solid #f0a8a8;
}

.sidebar-tier-budget-alert-icon {
  display: none;
}

.sidebar-tier-budget-alert-text {
  flex: 1;
  font-weight: 600;
}

.sidebar-tier-budget-alert-time {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  width: 100%;
}
</style>
