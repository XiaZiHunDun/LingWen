<!--
  CharacterRelationships.vue — Phase 117 (Task 14) 人物关系子组件
  从 useWorldDb().listRelationships('character', id) 拉取关系列表并渲染.
  当 characterId 变化时自动重新加载.
-->
<template>
  <section class="character-relationships" data-testid="character-relationships">
    <h3>关系</h3>
    <p v-if="!relationships.length">暂无关系</p>
    <ul v-else>
      <li
        v-for="rel in relationships"
        :key="rel.id"
        :data-testid="`relationship-${rel.id}`"
      >
        {{ rel.kind }} → {{ rel.target_kind }} #{{ rel.target_id }}
        <span v-if="rel.notes">({{ rel.notes }})</span>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'

const props = defineProps({
  characterId: { type: Number, required: true },
})

const { listRelationships } = useWorldDb()
const relationships = ref([])

async function load() {
  relationships.value = await listRelationships(
    'character', props.characterId,
  )
}

watch(() => props.characterId, load, { immediate: true })
</script>

<style scoped>
.character-relationships {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}
.character-relationships ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.character-relationships li {
  font-size: var(--text-sm);
}
</style>
