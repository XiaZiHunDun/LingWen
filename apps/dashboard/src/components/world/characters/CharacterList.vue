<!--
  CharacterList.vue — Phase 117 (Task 13) 人物卡列表 + canon-level 筛选
  列表渲染来自 useWorldDb().listCharacters(),按 store 的 canonLevelFilter 过滤.
  点击卡片打开选中态 (store.selectedCharacterId).
-->
<template>
  <div class="character-list" data-testid="character-list">
    <div class="character-list__filters character-filters" data-testid="character-filters">
      <button
        v-for="level in ['Draft', 'Provisional', 'Established']"
        :key="level"
        type="button"
        class="character-filter"
        :class="{ 'character-filter--active': store.canonLevelFilter === level }"
        :data-testid="`character-filter-${level}`"
        @click="store.setCanonLevelFilter(
          store.canonLevelFilter === level ? null : level)"
      >
        {{ level }}
      </button>
    </div>
    <div class="character-list__grid">
      <CharacterCard
        v-for="char in characters"
        :key="char.id"
        :character="char"
        @click="open(char)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import { useWorldStore } from '@/stores/useWorldStore'
import CharacterCard from './CharacterCard.vue'

const store = useWorldStore()
const { listCharacters } = useWorldDb()
const characters = ref([])

async function refresh() {
  characters.value = await listCharacters(store.canonLevelFilter || undefined)
}

function open(char) {
  store.selectedCharacterId = char.id
}

onMounted(refresh)
</script>

<style scoped>
.character-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.character-list__filters {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.character-filter {
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: var(--text-sm);
}
.character-filter--active {
  background: var(--color-accent, #4f8cff);
  color: var(--color-on-accent, #fff);
  border-color: transparent;
}
.character-list__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-sm);
}
</style>