<!--
  CharacterCard.vue — Phase 117 (Task 13) 人物卡卡片
  展示 character.name / canon_level / status,点击 emit('click') 由父级打开详情.
  颜色按 canon_level 区分 (draft / provisional / established).
-->
<template>
  <button
    type="button"
    class="character-card"
    :class="`character-card--${character.canon_level.toLowerCase()}`"
    :data-testid="`character-card-${character.slug}`"
    @click="$emit('click')"
  >
    <span class="character-card__name">{{ character.name }}</span>
    <span class="character-card__level">{{ character.canon_level }}</span>
    <span v-if="character.status" class="character-card__status">
      {{ character.status }}
    </span>
  </button>
</template>

<script setup>
defineProps({
  character: { type: Object, required: true },
})
defineEmits(['click'])
</script>

<style scoped>
.character-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  padding: var(--space-sm);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
  font: inherit;
}
.character-card--draft {
  border-style: dashed;
  opacity: 0.85;
}
.character-card--provisional {
  border-color: var(--color-warning, #f0a020);
}
.character-card--established {
  border-color: var(--color-accent, #4f8cff);
  font-weight: 500;
}
.character-card__name {
  font-size: var(--text-base);
}
.character-card__level {
  font-size: var(--text-xs);
  opacity: 0.7;
}
.character-card__status {
  font-size: var(--text-xs);
  opacity: 0.6;
}
</style>