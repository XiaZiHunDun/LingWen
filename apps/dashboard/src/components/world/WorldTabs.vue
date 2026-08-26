<!--
  WorldTabs.vue — Phase 117 (Task 12 / F) 世界页 tab 切换条
  4 个 tab: 人物卡 / 势力图 / 时间线 / 世界书
-->
<template>
  <div class="world-tabs" data-testid="world-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="world-tab"
      :class="{ 'world-tab--active': tab.id === activeTab }"
      :data-testid="`world-tab-${tab.id}`"
      @click="$emit('switch', tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  activeTab: { type: String, required: true },
})
defineEmits(['switch'])
const tabs = [
  { id: 'characters', label: '人物卡' },
  { id: 'factions', label: '势力图' },
  { id: 'timeline', label: '时间线' },
  { id: 'lore', label: '世界书' },
]
</script>

<style scoped>
.world-tabs {
  display: flex;
  gap: var(--space-xs);
  padding: var(--space-xs) 0;
  border-bottom: 1px solid var(--n-border-color);
}
.world-tab {
  padding: var(--space-xs) var(--space-md);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-text-dim);
}
.world-tab:hover {
  color: var(--color-accent);
}
.world-tab--active {
  color: var(--color-accent);
  background: var(--bg-muted);
  font-weight: 600;
}
</style>