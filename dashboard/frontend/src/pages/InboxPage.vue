<!--
  InboxPage.vue — Phase B: 待办统一入口（决策 + 一致性变更）
-->
<template>
  <div class="inbox-page l1-page" data-testid="inbox-page">
    <div class="l1-page__body l1-panel-enter hub-l1__panel">
      <PageLeadBar
        page-id="inbox"
        inline
        text="待决策与一致性审阅——日常写作请回「书桌」"
      />
    <HubPageHeader
      title="待办"
      subtitle="工作流确认 · 跨卷一致性变更"
      :meta="inboxMeta"
      meta-test-id="inbox-meta-line"
      :loading="hubLoading"
      @refresh="refreshActiveTab"
    >
      <template #actions>
        <button
          type="button"
          class="l1-pill"
          :class="{ 'l1-pill--primary': shareMessage === '已复制链接' }"
          data-testid="inbox-share-link-btn"
          @click="copyShareLink"
        >
          {{ shareMessage || '复制审阅链接' }}
        </button>
      </template>
    </HubPageHeader>

    <HubTabBar
      v-model="activeTab"
      :tabs="INBOX_TABS"
      :badges="inboxTabBadges"
      variant="segmented"
      test-id="inbox-tabs"
      class="inbox-tabs"
      @update:model-value="onTabChange"
    />

    <div class="hub-panel">
      <DecisionsPage v-if="activeTab === 'decisions'" ref="decisionsPanelRef" embedded />
      <RipplesPage v-else-if="activeTab === 'ripples'" ref="ripplesPanelRef" embedded />
    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import HubPageHeader from '../components/HubPageHeader.vue';
import HubTabBar from '../components/HubTabBar.vue';
import DecisionsPage from './DecisionsPage.vue';
import RipplesPage from './RipplesPage.vue';
import { INBOX_TABS } from '../config/dashboardNav.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { useDecisionStore } from '../composables/useDecisionStore.js';
import { useRippleStore } from '../composables/useRippleStore.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';
import { copyDashboardShareUrl } from '../utils/shareLink.js';

const { inboxTab, setInboxTab, focusChapter, focusDecisionId } = useDashboardNav();
const decisionStore = useDecisionStore();
const rippleStore = useRippleStore();
const ws = useWorkflowSocket();
const shareMessage = ref('');
const decisionsPanelRef = ref(null);
const ripplesPanelRef = ref(null);

const activeTab = computed({
  get: () => inboxTab.value,
  set: (tab) => setInboxTab(tab),
});

const pendingRipples = computed(() => {
  const stats = rippleStore.stats.value?.by_status;
  if (!stats) return 0;
  return Number(stats.pending ?? stats.PENDING ?? 0) || 0;
});

const pendingDecisions = computed(() =>
  ws.pendingDecisions.value.filter((d) => d.status === 'pending'),
);

const inboxMeta = computed(() => {
  const pending = pendingDecisions.value.length;
  const ripples = pendingRipples.value;
  return `待决策 ${pending} · 一致性待审 ${ripples}`;
});

const inboxTabBadges = computed(() => {
  const badges = {};
  const ripples = pendingRipples.value;
  if (ripples > 0) badges.ripples = String(ripples);
  const pending = pendingDecisions.value.length;
  if (pending > 0) badges.decisions = String(pending);
  return badges;
});

const hubLoading = computed(() => {
  if (activeTab.value === 'decisions') return decisionStore.loading.value;
  return rippleStore.loading.value;
});

onMounted(() => {
  if (activeTab.value !== 'ripples') {
    rippleStore.refresh().catch(() => {});
  }
});

function onTabChange(tab) {
  setInboxTab(tab);
}

async function refreshActiveTab() {
  if (activeTab.value === 'decisions') {
    await decisionStore.refresh();
    return;
  }
  await rippleStore.refresh();
}

async function copyShareLink() {
  const result = await copyDashboardShareUrl({
    nav: 'inbox',
    tab: activeTab.value,
    decision: focusDecisionId.value,
    chapter: focusChapter.value,
    role: 'reviewer',
  });
  shareMessage.value = result.ok ? '已复制链接' : '复制失败';
  if (result.ok) {
    setTimeout(() => { shareMessage.value = ''; }, 2000);
  }
}
</script>

<style scoped>
.inbox-page {
  flex: 1;
  min-height: 0;
}

.inbox-tabs {
  padding: 0;
}

.hub-panel :deep(.decisions-page),
.hub-panel :deep(.ripples-page) {
  padding-top: 0;
}
</style>
