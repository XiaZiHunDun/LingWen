<template>
  <ul
    v-if="deviations.length"
    class="deviation-list"
    data-testid="deviation-list"
  >
    <li
      v-for="(d, i) in deviations"
      :key="i"
      :class="[
        'deviation-item',
        `deviation-${d.severity}`,
        {
          'deviation-item--clickable': uiProfile.deviation_chapter_jump && d.chapter,
          'deviation-item--active': highlightEnabled && highlightedChapter === d.chapter,
        },
      ]"
      :role="uiProfile.deviation_chapter_jump && d.chapter ? 'button' : undefined"
      :tabindex="uiProfile.deviation_chapter_jump && d.chapter ? 0 : undefined"
      :data-testid="d.chapter ? `deviation-item-ch${d.chapter}` : `deviation-item-${i}`"
      @click="$emit('deviation-click', d)"
      @keydown.enter="$emit('deviation-click', d)"
    >
      <span v-if="d.chapter" class="deviation-chapter">ch{{ String(d.chapter).padStart(3, '0') }}</span>
      {{ d.message }}
    </li>
  </ul>
</template>

<script setup>
defineProps({
  deviations: { type: Array, default: () => [] },
  uiProfile: { type: Object, required: true },
  highlightEnabled: { type: Boolean, default: false },
  highlightedChapter: { type: Number, default: null },
});

defineEmits(['deviation-click']);
</script>

<style scoped>
.deviation-list {
  list-style: none;
  padding: 0;
  margin: var(--space-sm) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.deviation-item {
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  border-left: 3px solid var(--color-warning);
}

.deviation-item--clickable {
  cursor: pointer;
}

.deviation-item--clickable:hover {
  outline: 1px solid var(--color-accent);
}

.deviation-item--active {
  background: rgba(38, 168, 255, 0.12);
}

.deviation-chapter {
  font-weight: 600;
  margin-right: 6px;
}

.deviation-alert {
  border-left-color: var(--color-danger);
}

.deviation-warn {
  border-left-color: var(--color-warning);
}
</style>
