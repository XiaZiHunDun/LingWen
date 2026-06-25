<!--
  InsightPage.vue — Phase D: 洞察统一入口（追读力 + 分析，只读诊断）
-->
<template>
  <div class="insight-page" data-testid="insight-page">
    <header class="hub-header">
      <h1 class="page-title" data-testid="page-title">洞察</h1>
      <p class="hub-subtitle">追读力趋势 · 生产 KPI · 诊断只读</p>
    </header>

    <div
      v-if="isReadonlyInsight"
      class="readonly-banner pixel-border"
      data-testid="insight-readonly-banner"
    >
      审阅模式：本页仅查看诊断数据，不可发起生产或修改设定。
    </div>

    <HubTabBar
      v-model="activeTab"
      :tabs="INSIGHT_TABS"
      test-id="insight-tabs"
      @update:model-value="onTabChange"
    />

    <div class="hub-panel">
      <OverviewPage v-if="activeTab === 'overview'" />
      <AnalyticsPage v-else-if="activeTab === 'analytics'" />
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue';
import HubTabBar from '../components/HubTabBar.vue';
import OverviewPage from './OverviewPage.vue';
import AnalyticsPage from './AnalyticsPage.vue';
import { INSIGHT_TABS } from '../config/dashboardNav.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';

const isReadonlyInsight = inject('isReadonlyInsight', computed(() => false));
const { insightTab, setInsightTab } = useDashboardNav();

const activeTab = computed({
  get: () => insightTab.value,
  set: (tab) => setInsightTab(tab),
});

function onTabChange(tab) {
  setInsightTab(tab);
}
</script>

<style scoped>
.insight-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.hub-header {
  padding: 0 var(--space-md);
}

.page-title {
  font-size: var(--text-xl);
  font-family: var(--font-ui);
  font-weight: 700;
}

.hub-subtitle {
  margin-top: var(--space-xs);
  font-size: var(--text-sm);
  color: var(--color-text-dim);
}

.readonly-banner {
  margin: 0 var(--space-md);
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-sm);
  background: var(--bg-secondary);
  color: var(--color-text-dim);
}

.hub-panel :deep(.overview-page),
.hub-panel :deep(.analytics-page) {
  padding-top: 0;
}

.hub-panel :deep(.page-header .page-title) {
  display: none;
}
</style>
