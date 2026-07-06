<!--
  CreatorWorkspaceShell.vue — 工作区标签栏 + 三栏网格（inject 页级 chrome 上下文）
-->
<template>
  <div
    v-if="c.overview"
    class="creator-workspace-shell"
    :class="{ 'creator-workspace-shell--tabbed': c.workspaceTabsEnabled }"
  >
  <div
    v-if="c.overview && c.workspaceTabsEnabled"
    class="creator-workspace-tab-row"
  >
    <HubTabBar
      v-model="c.workspaceActiveTab"
      :tabs="c.workspacePrimaryTabs"
      :badges="c.workspaceTabBadges"
      variant="segmented"
      test-id="creator-workspace-tab"
      class="creator-workspace-tabs"
      data-testid="creator-workspace-tabs"
    />

    <nav
      v-if="c.workspaceSecondaryTabs?.length"
      class="creator-workspace-secondary-tabs"
      data-testid="creator-workspace-secondary-tabs"
    >
      <button
        v-for="tab in c.workspaceSecondaryTabs"
        :key="tab.id"
        type="button"
        class="hub-tab hub-tab--secondary"
        :class="{ 'hub-tab--active': c.workspaceActiveTab === tab.id }"
        :data-testid="`creator-workspace-tab-${tab.id}`"
        @click="c.setWorkspaceTab(tab.id)"
      >
        <span v-if="tab.icon" class="hub-tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
        <span v-if="c.workspaceTabBadges?.[tab.id]" class="hub-tab-badge">{{ c.workspaceTabBadges[tab.id] }}</span>
      </button>
    </nav>

    <nav
      v-if="c.deskDrawerEnabled && c.workspaceDrawerTabs?.length"
      class="creator-desk-drawer-triggers"
      data-testid="creator-desk-drawer-triggers"
    >
      <button
        v-for="tab in c.workspaceDrawerTabs"
        :key="tab.id"
        type="button"
        class="hub-tab hub-tab--drawer"
        :class="{ 'hub-tab--active': c.deskDrawerPanel === tab.id }"
        :data-testid="`creator-desk-drawer-${tab.id}`"
        @click="c.openDeskDrawer(tab.id)"
      >
        <span v-if="tab.icon" class="hub-tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
        <span v-if="c.workspaceTabBadges?.[tab.id]" class="hub-tab-badge">{{ c.workspaceTabBadges[tab.id] }}</span>
      </button>
    </nav>
  </div>

  <div
    v-if="c.deskDrawerEnabled && c.deskDrawerOpen"
    class="desk-drawer-backdrop"
    data-testid="creator-desk-drawer-backdrop"
    @click="c.closeDeskDrawer()"
  />

  <div
    v-if="c.overview"
    :key="c.workspaceActiveTab"
    class="creator-grid l1-panel-enter"
    :class="{ 'creator-grid--tabbed': c.workspaceTabsEnabled }"
    data-testid="creator-grid"
  >
    <slot />
  </div>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import HubTabBar from '../HubTabBar.vue';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';

const c = inject(CREATOR_PAGE_CHROME_KEY);
</script>

<style scoped>
.creator-workspace-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.creator-workspace-shell--tabbed .creator-workspace-tab-row {
  flex-shrink: 0;
}

.creator-workspace-tab-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  padding: 0;
  margin-bottom: var(--space-sm);
}

.creator-workspace-tabs {
  padding: 0;
  margin-bottom: 0;
}

.creator-workspace-secondary-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-left: auto;
}

.hub-tab--secondary {
  font-size: var(--text-xs);
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-dim);
  font-weight: 500;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.hub-tab--secondary:hover {
  background: var(--bg-muted);
  color: var(--color-text);
}

.hub-tab--secondary.hub-tab--active {
  background: var(--color-accent-soft);
  color: var(--color-accent);
  opacity: 1;
  font-weight: 600;
}

.creator-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  align-items: start;
}

.creator-grid--tabbed {
  grid-template-columns: 1fr;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

@media (max-width: 960px) {
  .creator-grid {
    grid-template-columns: 1fr;
  }

  .creator-workspace-tab-row {
    flex-direction: column;
    align-items: stretch;
  }

  .creator-workspace-secondary-tabs {
    margin-left: 0;
  }
}
</style>
