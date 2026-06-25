<!--
  ProducePage.vue — Phase B: 生产统一入口（工作室 + 章节 + 工作流）
-->
<template>
  <div class="produce-page" data-testid="produce-page">
    <header class="hub-header">
      <h1 class="page-title" data-testid="page-title">生产</h1>
      <p class="hub-subtitle">Preflight · Batch · 章节记录 · 工作流调度</p>
    </header>

    <HubTabBar
      v-model="activeTab"
      :tabs="PRODUCE_TABS"
      test-id="produce-tabs"
      @update:model-value="onTabChange"
    />

    <div class="hub-panel">
      <StudioPage v-if="activeTab === 'studio'" />
      <ChaptersPage v-else-if="activeTab === 'chapters'" />
      <WorkflowsPage v-else-if="activeTab === 'workflows'" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import HubTabBar from '../components/HubTabBar.vue';
import StudioPage from './StudioPage.vue';
import ChaptersPage from './ChaptersPage.vue';
import WorkflowsPage from './WorkflowsPage.vue';
import { PRODUCE_TABS } from '../config/dashboardNav.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';

const { produceTab, setProduceTab } = useDashboardNav();

const activeTab = computed({
  get: () => produceTab.value,
  set: (tab) => setProduceTab(tab),
});

function onTabChange(tab) {
  setProduceTab(tab);
}
</script>

<style scoped>
.produce-page {
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

.hub-panel :deep(.studio-page),
.hub-panel :deep(.chapters-page),
.hub-panel :deep(.workflows-page) {
  padding-top: 0;
}

.hub-panel :deep(.page-header .page-title) {
  display: none;
}
</style>
