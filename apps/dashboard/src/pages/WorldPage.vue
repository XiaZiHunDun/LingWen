<!--
  WorldPage.vue — Phase 117 (Task 12 / F) 世界页 skeleton
  /world route 入口,组成: PageLeadBar + WorldTabs + 4 个 tab 占位 stub.
  完整实现 (列表/编辑器/Graph/审核 inbox) 在 Phase 117 follow-up tasks.
-->
<template>
  <div class="world-page l1-page" data-testid="world-page">
    <PageLeadBar
      page-id="world"
      inline
      text="人物 · 势力 · 时间线 · 世界书 — 单源真相"
    />
    <div class="l1-page__body l1-panel-enter hub-l1__panel">
      <WorldTabs :active-tab="store.activeTab" @switch="store.switchTab" />
      <div class="world-page__body">
        <CharacterList v-if="store.activeTab === 'characters'" />
        <FactionGraph v-else-if="store.activeTab === 'factions'" />
        <TimelineView v-else-if="store.activeTab === 'timeline'" />
        <LoreList v-else-if="store.activeTab === 'lore'" />
      </div>
    </div>
  </div>
</template>

<script setup>
import PageLeadBar from '@/components/PageLeadBar.vue'
import { useWorldStore } from '@/stores/useWorldStore'
import WorldTabs from '@/components/world/WorldTabs.vue'
import CharacterList from '@/components/world/characters/CharacterList.vue'
import FactionGraph from '@/components/world/factions/FactionGraph.vue'
import TimelineView from '@/components/world/timeline/TimelineView.vue'
import LoreList from '@/components/world/lore/LoreList.vue'

const store = useWorldStore()
</script>

<style scoped>
.world-page__body {
  padding-top: var(--space-md);
}
</style>