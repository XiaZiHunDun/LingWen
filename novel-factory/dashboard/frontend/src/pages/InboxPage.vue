<!--
  InboxPage.vue — Phase B: 待办统一入口（决策 + 一致性变更）
-->
<template>
  <div class="inbox-page" data-testid="inbox-page">
    <header class="hub-header">
      <div>
        <h1 class="page-title" data-testid="page-title">待办</h1>
        <p class="hub-subtitle">工作流确认 · 跨卷一致性变更</p>
      </div>
      <button
        type="button"
        class="share-link-btn pixel-border"
        data-testid="inbox-share-link-btn"
        @click="copyShareLink"
      >
        {{ shareMessage || '复制审阅链接' }}
      </button>
    </header>

    <HubTabBar
      v-model="activeTab"
      :tabs="INBOX_TABS"
      test-id="inbox-tabs"
      @update:model-value="onTabChange"
    />

    <div class="hub-panel">
      <DecisionsPage v-if="activeTab === 'decisions'" />
      <RipplesPage v-else-if="activeTab === 'ripples'" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import HubTabBar from '../components/HubTabBar.vue';
import DecisionsPage from './DecisionsPage.vue';
import RipplesPage from './RipplesPage.vue';
import { INBOX_TABS } from '../config/dashboardNav.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { copyDashboardShareUrl } from '../utils/shareLink.js';

const { inboxTab, setInboxTab, focusChapter, focusDecisionId } = useDashboardNav();
const shareMessage = ref('');

const activeTab = computed({
  get: () => inboxTab.value,
  set: (tab) => setInboxTab(tab),
});

function onTabChange(tab) {
  setInboxTab(tab);
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
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.hub-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  padding: 0 var(--space-md);
}

.share-link-btn {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  padding: 8px 12px;
  background: var(--bg-secondary);
  cursor: pointer;
  white-space: nowrap;
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

.hub-panel :deep(.decisions-page),
.hub-panel :deep(.ripples-page) {
  padding-top: 0;
}

.hub-panel :deep(.page-header .page-title) {
  display: none;
}
</style>
