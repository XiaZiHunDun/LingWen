<!--
  InsightPage.vue — Phase D: 洞察统一入口（追读力 + 分析，只读诊断）
-->
<template>
  <div class="insight-page l1-page" data-testid="insight-page">
    <div class="l1-page__body l1-panel-enter hub-l1__panel">
      <PageLeadBar
        page-id="insight"
        inline
        text="追读力与健康度诊断——只读查看，不可发起生产"
      />
    <HubPageHeader
      title="洞察"
      :subtitle="insightSubtitle"
      :loading="hubLoading"
      @refresh="refreshActiveTab"
    />

    <div
      v-if="isReadonlyInsight"
      class="readonly-banner pixel-border"
      data-testid="insight-readonly-banner"
    >
      <span class="readonly-banner-icon" aria-hidden="true">👁</span>
      <span>审阅模式：本页仅查看诊断数据，不可发起生产或修改设定。</span>
    </div>

    <HubTabBar
      v-model="activeTab"
      :tabs="INSIGHT_TABS"
      variant="segmented"
      test-id="insight-tabs"
      class="insight-tabs"
      @update:model-value="onTabChange"
    />

    <div class="hub-panel">
      <OverviewPage v-if="activeTab === 'overview'" embedded />
      <AnalyticsPage v-else-if="activeTab === 'analytics'" embedded />
    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import HubPageHeader from '../components/HubPageHeader.vue';
import HubTabBar from '../components/HubTabBar.vue';
import OverviewPage from './OverviewPage.vue';
import AnalyticsPage from './AnalyticsPage.vue';
import { INSIGHT_TABS } from '../config/dashboardNav.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { useOverviewStore } from '../composables/useOverviewStore.js';
import { useRippleStore } from '../composables/useRippleStore.js';

const isReadonlyInsight = inject('isReadonlyInsight', computed(() => false));
const { insightTab, setInsightTab } = useDashboardNav();
const overviewStore = useOverviewStore();
const rippleStore = useRippleStore();

const activeTab = computed({
  get: () => insightTab.value,
  set: (tab) => setInsightTab(tab),
});

const insightSubtitle = computed(() => {
  if (isReadonlyInsight.value) {
    return activeTab.value === 'analytics'
      ? '审阅视图 · 生产 KPI 只读'
      : '审阅视图 · 追读力只读';
  }
  return activeTab.value === 'analytics'
    ? '生产 KPI · 成本与涟漪统计'
    : '追读力趋势 · 钩子与爽点';
});

const hubLoading = computed(() => {
  if (activeTab.value === 'overview') return overviewStore.loading.value;
  return rippleStore.loading.value;
});

function onTabChange(tab) {
  setInsightTab(tab);
}

async function refreshActiveTab() {
  if (activeTab.value === 'overview') {
    await overviewStore.refresh();
    return;
  }
  await Promise.all([
    overviewStore.refresh(),
    rippleStore.refresh(),
  ]);
}
</script>

<style scoped>
.insight-page {
  flex: 1;
  min-height: 0;
}

.insight-tabs {
  padding: 0;
}

.readonly-banner {
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-sm);
  background: var(--bg-muted);
  color: var(--color-text);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--color-accent);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.readonly-banner-icon {
  font-size: var(--text-md);
}

.hub-panel :deep(.overview-page),
.hub-panel :deep(.analytics-page) {
  padding-top: 0;
}
</style>
