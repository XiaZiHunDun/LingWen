<!--
  CreatorInlineConflictGutter.vue — 正文旁冲突标记（段落级跳转）
-->
<template>
  <aside class="inline-conflict-gutter" data-testid="write-inline-conflict-gutter">
    <p class="inline-conflict-gutter__title">冲突</p>
    <ul class="inline-conflict-gutter__list">
      <li
        v-for="marker in markers"
        :key="marker.id"
        class="inline-conflict-gutter__item-wrap"
      >
        <button
          type="button"
          class="inline-conflict-gutter__item"
          :class="[
            `inline-conflict-gutter__item--${marker.level}`,
            { 'inline-conflict-gutter__item--active': marker.id === activeId },
          ]"
          :data-testid="`inline-conflict-${marker.kind}`"
          :title="markerTooltip(marker)"
          @click="$emit('focus', marker)"
        >
          <span class="inline-conflict-gutter__icon" aria-hidden="true">{{ kindIcon(marker.kind) }}</span>
          <span class="inline-conflict-gutter__badge">{{ kindBadge(marker.kind) }}</span>
          <span class="inline-conflict-gutter__label">{{ marker.label }}</span>
          <span v-if="marker.paragraph" class="inline-conflict-gutter__para">¶{{ marker.paragraph }}</span>
        </button>
      </li>
    </ul>
  </aside>
</template>

<script setup>
defineProps({
  markers: { type: Array, default: () => [] },
  activeId: { type: String, default: null },
});

defineEmits(['focus']);

function kindIcon(kind) {
  if (kind === 'logic') return '⊘';
  if (kind === 'deviation') return '↗';
  if (kind === 'light') return '✎';
  return '·';
}

function kindBadge(kind) {
  if (kind === 'logic') return '逻辑';
  if (kind === 'deviation') return '偏离';
  if (kind === 'light') return '提示';
  return '冲突';
}

function markerTooltip(marker) {
  const parts = [marker.label];
  if (marker.fixHint) parts.push(marker.fixHint);
  if (marker.paragraph) parts.push(`段落 ${marker.paragraph}`);
  return parts.join(' · ');
}
</script>

<style scoped>
.inline-conflict-gutter {
  width: 132px;
  flex-shrink: 0;
  padding: var(--space-xs);
  border: 1px solid var(--border-color);
  background: var(--color-danger-soft);
  font-size: 10px;
  max-height: 220px;
  overflow-y: auto;
}
.inline-conflict-gutter__title {
  margin: 0 0 4px;
  font-weight: 600;
  font-size: var(--text-xs);
}
.inline-conflict-gutter__list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.inline-conflict-gutter__item-wrap {
  list-style: none;
  margin: 0;
  padding: 0;
}
.inline-conflict-gutter__item {
  width: 100%;
  padding: 4px 2px;
  border: none;
  border-bottom: 1px dashed var(--border-subtle, var(--border-color));
  cursor: pointer;
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  align-items: baseline;
  background: transparent;
  font: inherit;
  color: inherit;
  text-align: left;
}
.inline-conflict-gutter__item--error { border-left: 2px solid var(--color-danger); }
.inline-conflict-gutter__item--warn { border-left: 2px solid var(--color-warning); }
.inline-conflict-gutter__item--active {
  background: var(--color-warning-soft);
}
.inline-conflict-gutter__icon {
  font-size: 10px;
  opacity: 0.75;
  width: 1em;
}
.inline-conflict-gutter__badge {
  font-size: 9px;
  opacity: 0.8;
}
.inline-conflict-gutter__label {
  flex: 1;
  min-width: 0;
  line-height: 1.3;
}
.inline-conflict-gutter__para {
  opacity: 0.7;
}

@media (prefers-reduced-motion: reduce) {
  .inline-conflict-gutter__item--active {
    transition: none;
  }
}
</style>
