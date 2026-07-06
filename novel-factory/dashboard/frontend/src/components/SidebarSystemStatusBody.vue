<!--
  SidebarSystemStatusBody.vue — 人类习惯侧栏「系统状态」展开内容（始终有可读信息）
-->
<template>
  <div class="sidebar-system-status" data-testid="sidebar-system-status-body">
    <dl class="sidebar-system-status__rows">
      <div class="sidebar-system-status__row" data-testid="sidebar-system-api-row">
        <dt>接口</dt>
        <dd :class="apiStateClass">{{ apiLabel }}</dd>
      </div>
      <div class="sidebar-system-status__row" data-testid="sidebar-system-ws-row">
        <dt>实时同步</dt>
        <dd :class="wsStateClass">{{ wsLabel }}</dd>
      </div>
    </dl>

    <SidebarTierBudgetAlerts :status="status" />
    <SidebarCostBanner :status="status" />

    <p
      v-if="showHealthyHint"
      class="sidebar-system-status__hint"
      data-testid="sidebar-system-healthy-hint"
    >
      暂无成本告警，可放心写作。
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import SidebarCostBanner from './SidebarCostBanner.vue';
import SidebarTierBudgetAlerts from './SidebarTierBudgetAlerts.vue';
import { useTierBudgetAlerts } from '../composables/useTierBudgetAlerts.js';

const props = defineProps({
  status: {
    type: Object,
    default: () => ({}),
  },
  apiOffline: { type: Boolean, default: false },
  apiChecking: { type: Boolean, default: false },
  wsConnected: { type: Boolean, default: false },
});

const { alerts } = useTierBudgetAlerts();

const hasCost = computed(() => {
  const scenario = props.status?.cost_by_scenario ?? {};
  const tier = props.status?.cost_by_tier ?? {};
  const scenarioHas = Object.values(scenario).some((v) => Number(v) > 0);
  const tierHas = Object.values(tier).some((v) => Number(v) > 0);
  return scenarioHas || tierHas;
});

const showHealthyHint = computed(
  () => !props.apiOffline && props.wsConnected && alerts.value.length === 0 && !hasCost.value,
);

const apiLabel = computed(() => {
  if (props.apiChecking) return '检测中…';
  return props.apiOffline ? '不可用' : '正常';
});

const apiStateClass = computed(() => {
  if (props.apiChecking) return 'is-pending';
  return props.apiOffline ? 'is-warn' : 'is-ok';
});

const wsLabel = computed(() => (props.wsConnected ? '已连接' : '未连接'));

const wsStateClass = computed(() => (props.wsConnected ? 'is-ok' : 'is-warn'));
</script>

<style scoped>
.sidebar-system-status {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.sidebar-system-status__rows {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sidebar-system-status__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  font-size: var(--text-xs);
  line-height: 1.4;
}

.sidebar-system-status__row dt {
  margin: 0;
  color: var(--color-text-dim);
  font-weight: 500;
}

.sidebar-system-status__row dd {
  margin: 0;
  font-weight: 600;
  text-align: right;
}

.sidebar-system-status__row dd.is-ok {
  color: var(--color-success);
}

.sidebar-system-status__row dd.is-warn {
  color: var(--color-warning);
}

.sidebar-system-status__row dd.is-pending {
  color: var(--color-text-dim);
}

.sidebar-system-status__hint {
  margin: 0;
  padding: 8px 10px;
  font-size: var(--text-xs);
  line-height: 1.45;
  color: var(--color-text-secondary);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  box-shadow: inset 0 0 0 1px var(--border-color);
}
</style>
