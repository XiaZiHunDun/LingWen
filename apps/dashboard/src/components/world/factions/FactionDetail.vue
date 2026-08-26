<!--
  FactionDetail.vue — Phase 117 (Task 16) 势力详情侧栏
  展示选中势力的 name / description,通过 emit('close') 由父级关闭.
-->
<template>
  <aside class="faction-detail" data-testid="faction-detail">
    <button
      type="button"
      class="faction-detail__close faction-detail-close"
      data-testid="faction-detail-close"
      @click="$emit('close')"
    >关闭</button>
    <h2 class="faction-detail__name">{{ faction?.name }}</h2>
    <p v-if="faction" class="faction-detail__description">{{ faction.description }}</p>
  </aside>
</template>

<script setup>
defineProps({
  faction: { type: Object, default: null },
})
defineEmits(['close'])
</script>

<style scoped>
.faction-detail {
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
.faction-detail-close,
.faction-detail__close {
  align-self: flex-end;
  background: transparent;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font: inherit;
  color: inherit;
  padding: 0.125rem 0.5rem;
}
.faction-detail__name {
  margin: 0;
  font-size: var(--text-lg);
}
.faction-detail__description {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.85;
  white-space: pre-wrap;
}
</style>