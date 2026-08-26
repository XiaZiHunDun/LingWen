<!--
  FactionGraph.vue — Phase 117 (Task 16) 势力页 — 列表 / 关系图 切换
  - 默认 viewMode='list' 显示势力卡片列表,点击打开详情侧栏.
  - 切换到 viewMode='graph' 渲染 FactionGraphCanvas (Task 17 完整 cytoscape 图).
  - 选中状态通过 store.selectedCharacterId 共享 (复用 Task 13 / 14 的 store 字段).
-->
<template>
  <div class="faction-graph-page" data-testid="faction-graph-page">
    <div class="faction-graph-page__toolbar">
      <button
        type="button"
        class="faction-graph-page__list-toggle faction-graph-view-list faction-list-toggle"
        :class="{ 'is-active': viewMode === 'list' }"
        data-testid="faction-graph-view-list"
        @click="viewMode = 'list'"
      >列表</button>
      <button
        type="button"
        class="faction-graph-page__graph-toggle faction-graph-view-graph faction-graph-toggle"
        :class="{ 'is-active': viewMode === 'graph' }"
        data-testid="faction-graph-view-graph"
        @click="viewMode = 'graph'"
      >关系图</button>
    </div>
    <div v-if="viewMode === 'list'" class="faction-list" data-testid="faction-list">
      <button
        v-for="f in factions"
        :key="f.id"
        type="button"
        class="faction-card faction-card-btn"
        :class="{ 'is-selected': selectedFaction && selectedFaction.id === f.id }"
        :data-testid="`faction-card-${f.slug}`"
        @click="open(f)"
      >
        {{ f.name }}
      </button>
    </div>
    <FactionGraphCanvas
      v-else
      :factions="factions"
      :relationships="relationships"
    />
    <FactionDetail v-if="selectedFaction" :faction="selectedFaction" @close="store.selectedCharacterId = null" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import { useWorldStore } from '@/stores/useWorldStore'
import FactionGraphCanvas from './FactionGraphCanvas.vue'
import FactionDetail from './FactionDetail.vue'

const store = useWorldStore()
const { listFactions, listRelationships } = useWorldDb()
const factions = ref([])
const relationships = ref([])
const viewMode = ref('list')

const selectedFaction = computed(() => {
  if (!store.selectedCharacterId) return null
  return factions.value.find((f) => f.id === store.selectedCharacterId) || null
})

async function refresh() {
  factions.value = await listFactions()
  relationships.value = await listRelationships()
}

function open(faction) {
  store.selectedCharacterId = faction.id
}

onMounted(refresh)
</script>

<style scoped>
.faction-graph-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.faction-graph-page__toolbar {
  display: flex;
  gap: var(--space-sm);
}
.faction-list-toggle,
.faction-graph-toggle {
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: var(--text-sm);
}
.faction-list-toggle.is-active,
.faction-graph-toggle.is-active {
  background: var(--color-accent, #4f8cff);
  color: var(--color-on-accent, #fff);
  border-color: transparent;
}
.faction-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-sm);
}
.faction-card,
.faction-card-btn {
  display: flex;
  align-items: flex-start;
  padding: var(--space-sm);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
  font: inherit;
}
.faction-card.is-selected,
.faction-card-btn.is-selected {
  border-color: var(--color-accent, #4f8cff);
  background: var(--bg-muted);
  font-weight: 500;
}
</style>