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
        class="inline-conflict-gutter__item"
        :class="[
          `inline-conflict-gutter__item--${marker.level}`,
          { 'inline-conflict-gutter__item--active': marker.id === activeId },
        ]"
        :data-testid="`inline-conflict-${marker.kind}`"
        role="button"
        tabindex="0"
        @click="$emit('focus', marker)"
        @keydown.enter="$emit('focus', marker)"
      >
        <span class="inline-conflict-gutter__badge">{{ marker.kind === 'logic' ? '逻辑' : '偏离' }}</span>
        <span class="inline-conflict-gutter__label">{{ marker.label }}</span>
        <span v-if="marker.paragraph" class="inline-conflict-gutter__para">¶{{ marker.paragraph }}</span>
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
</script>

<style scoped>
.inline-conflict-gutter {
  width: 132px;
  flex-shrink: 0;
  padding: var(--space-xs);
  border: 1px solid var(--border-color);
  background: rgba(200, 80, 80, 0.04);
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
.inline-conflict-gutter__item {
  padding: 4px 2px;
  border-bottom: 1px dashed var(--border-color);
  cursor: pointer;
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  align-items: baseline;
}
.inline-conflict-gutter__item--error { border-left: 2px solid #c44; }
.inline-conflict-gutter__item--warn { border-left: 2px solid #aa8; }
.inline-conflict-gutter__item--active {
  background: rgba(255, 220, 100, 0.35);
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
</style>
