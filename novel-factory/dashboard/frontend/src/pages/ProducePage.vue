<!--
  ProducePage.vue — Phase B: 生产统一入口（工作室 + 章节 + 工作流）
-->
<template>
  <div class="produce-page l1-page" data-testid="produce-page">
    <div class="l1-page__body l1-panel-enter hub-l1__panel">
      <PageLeadBar
        page-id="produce"
        inline
        text="批量生成与工作流——日常写作请回「书桌」"
      />
    <HubPageHeader
      title="生产"
      subtitle="Preflight · Batch · 章节记录 · 工作流调度"
      :loading="hubLoading"
      @refresh="refreshActiveTab"
    />

    <HubTabBar
      v-model="activeTab"
      :tabs="visibleProduceTabs"
      variant="segmented"
      test-id="produce-tabs"
      class="produce-tabs"
      @update:model-value="onTabChange"
    />

    <div class="hub-panel">
      <StudioPage v-if="activeTab === 'studio'" embedded />
      <ChaptersPage v-else-if="activeTab === 'chapters'" ref="chaptersPanelRef" embedded />
      <WorkflowsPage v-else-if="activeTab === 'workflows'" ref="workflowsPanelRef" embedded />
    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import HubPageHeader from '../components/HubPageHeader.vue';
import HubTabBar from '../components/HubTabBar.vue';
import StudioPage from './StudioPage.vue';
import ChaptersPage from './ChaptersPage.vue';
import WorkflowsPage from './WorkflowsPage.vue';
import { PRODUCE_TABS } from '../config/dashboardNav.js';
import { isHubProduceTabVisible } from '../config/creatorPanelMatrix.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { useStudioProject } from '../composables/useStudioProject.js';

const { produceTab, setProduceTab } = useDashboardNav();
const studio = useStudioProject();
const chaptersPanelRef = ref(null);
const workflowsPanelRef = ref(null);

const activeTab = computed({
  get: () => produceTab.value,
  set: (tab) => setProduceTab(tab),
});

const visibleProduceTabs = computed(() => {
  const mode = studio.summary.value?.creation_mode;
  if (!mode) return PRODUCE_TABS;
  return PRODUCE_TABS.filter((tab) => isHubProduceTabVisible(mode, tab.id));
});

watch(
  () => [studio.summary.value?.creation_mode, visibleProduceTabs.value.map((t) => t.id).join(',')],
  () => {
    const ids = visibleProduceTabs.value.map((t) => t.id);
    if (ids.length && !ids.includes(activeTab.value)) {
      setProduceTab(ids[0]);
    }
  },
  { immediate: true },
);

const hubLoading = computed(() => {
  if (activeTab.value === 'studio') return studio.loading.value;
  if (activeTab.value === 'chapters') return chaptersPanelRef.value?.loading ?? false;
  if (activeTab.value === 'workflows') return workflowsPanelRef.value?.loading ?? false;
  return false;
});

function onTabChange(tab) {
  setProduceTab(tab);
}

async function refreshActiveTab() {
  if (activeTab.value === 'studio') {
    await studio.refresh();
    return;
  }
  if (activeTab.value === 'chapters') {
    await chaptersPanelRef.value?.refreshAll?.();
    return;
  }
  if (activeTab.value === 'workflows') {
    await workflowsPanelRef.value?.refresh?.();
  }
}
</script>

<style scoped>
.produce-page {
  flex: 1;
  min-height: 0;
}

.produce-tabs {
  padding: 0;
}

.hub-panel :deep(.studio-page),
.hub-panel :deep(.chapters-page),
.hub-panel :deep(.workflows-page) {
  padding-top: 0;
}
</style>
