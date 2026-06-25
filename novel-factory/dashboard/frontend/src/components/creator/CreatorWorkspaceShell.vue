<!--
  CreatorWorkspaceShell.vue — 工作区标签栏 + 三栏网格（inject 页级 chrome 上下文）
-->
<template>
  <HubTabBar
    v-if="c.overview && c.workspaceTabsEnabled"
    v-model="c.workspaceActiveTab"
    :tabs="c.workspaceTabs"
    :badges="c.workspaceTabBadges"
    test-id="creator-workspace-tab"
    class="creator-workspace-tabs"
    data-testid="creator-workspace-tabs"
  />

  <div
    v-if="c.overview"
    class="creator-grid"
    :class="{ 'creator-grid--tabbed': c.workspaceTabsEnabled }"
    data-testid="creator-grid"
  >
    <slot />
  </div>
</template>

<script setup>
import { inject } from 'vue';
import HubTabBar from '../HubTabBar.vue';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';

const c = inject(CREATOR_PAGE_CHROME_KEY);
</script>

<style scoped>
.creator-workspace-tabs {
  padding: 0 var(--space-md);
}

.creator-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  align-items: start;
}

.creator-grid--tabbed {
  grid-template-columns: 1fr;
}

@media (max-width: 960px) {
  .creator-grid {
    grid-template-columns: 1fr;
  }
}
</style>
