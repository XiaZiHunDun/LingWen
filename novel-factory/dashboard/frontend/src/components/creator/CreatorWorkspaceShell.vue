<!--
  CreatorWorkspaceShell.vue — 工作区标签栏 + 三栏网格（从 CreatorPage 拆出）
-->
<template>
  <HubTabBar
    v-if="overview && tabsEnabled"
    :model-value="activeTab"
    :tabs="workspaceTabs"
    :badges="tabBadges"
    test-id="creator-workspace-tab"
    class="creator-workspace-tabs"
    data-testid="creator-workspace-tabs"
    @update:model-value="$emit('update:activeTab', $event)"
  />

  <div
    v-if="overview"
    class="creator-grid"
    :class="{ 'creator-grid--tabbed': tabsEnabled }"
    data-testid="creator-grid"
  >
    <slot />
  </div>
</template>

<script setup>
import HubTabBar from '../HubTabBar.vue';

defineProps({
  overview: { type: Object, default: null },
  tabsEnabled: { type: Boolean, required: true },
  activeTab: { type: String, required: true },
  workspaceTabs: { type: Array, required: true },
  tabBadges: { type: Object, default: null },
});

defineEmits(['update:activeTab']);
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
