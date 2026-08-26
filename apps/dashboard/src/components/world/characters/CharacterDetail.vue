<!--
  CharacterDetail.vue — Phase 117 (Task 14) 人物详情侧栏
  从 useWorldDb().getCharacter(id) 拉取详情,渲染姓名 / slug / canon-level / attributes.
  嵌入 CharacterRelationships 子组件展示关系列表.
  通过 emit('close') 由父级关闭.
-->
<template>
  <aside class="character-detail" data-testid="character-detail">
    <header>
      <button
        type="button"
        class="character-detail-close character-detail__close"
        data-testid="character-detail-close"
        @click="$emit('close')"
      >关闭</button>
    </header>
    <div v-if="loading" class="character-detail__loading">加载中…</div>
    <div v-else-if="character">
      <h2 class="character-detail__name">{{ character.name }}</h2>
      <p class="character-detail__slug">slug: {{ character.slug }}</p>
      <p class="character-detail__canon">{{ character.canon_level }}</p>
      <section v-if="character.attributes">
        <h3>设定</h3>
        <pre>{{ JSON.stringify(character.attributes, null, 2) }}</pre>
      </section>
      <CharacterRelationships :character-id="character.id" />
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import CharacterRelationships from './CharacterRelationships.vue'

const props = defineProps({
  characterId: { type: Number, required: true },
})
defineEmits(['close'])

const { getCharacter } = useWorldDb()
const character = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    character.value = await getCharacter(props.characterId)
  } finally {
    loading.value = false
  }
}

watch(() => props.characterId, load, { immediate: true })
</script>

<style scoped>
.character-detail {
  position: sticky;
  top: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, transparent);
}
.character-detail-close,
.character-detail__close {
  align-self: flex-end;
  background: transparent;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font: inherit;
  color: inherit;
  padding: 0.125rem 0.5rem;
}
.character-detail__name {
  margin: 0;
  font-size: var(--text-lg);
}
.character-detail__slug,
.character-detail__canon {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.75;
}
.character-detail__loading {
  font-size: var(--text-sm);
  opacity: 0.6;
}
.character-detail pre {
  margin: 0;
  font-size: var(--text-xs);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
