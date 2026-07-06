<!--
  CreatorChapterBodyEditor.vue — 正文区 + 冲突 gutter
-->
<template>
  <div class="chapter-body-editor" data-testid="chapter-body-editor">
    <CreatorInlineConflictGutter
      v-if="showGutter && markers.length"
      :markers="markers"
      :active-id="activeMarkerId"
      @focus="$emit('focus-marker', $event)"
    />
    <div class="chapter-body-editor__main">
      <slot />
    </div>
  </div>
</template>

<script setup>
import CreatorInlineConflictGutter from './CreatorInlineConflictGutter.vue';

defineProps({
  showGutter: { type: Boolean, default: false },
  markers: { type: Array, default: () => [] },
  activeMarkerId: { type: String, default: null },
});

defineEmits(['focus-marker']);
</script>

<style scoped>
.chapter-body-editor {
  display: flex;
  gap: var(--space-xs);
  align-items: flex-start;
}
.chapter-body-editor__main {
  flex: 1;
  min-width: 0;
}
</style>
