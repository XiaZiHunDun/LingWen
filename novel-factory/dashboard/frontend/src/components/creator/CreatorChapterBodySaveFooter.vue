<!--
  CreatorChapterBodySaveFooter.vue — 正文保存状态 + 手动保存
-->
<template>
  <div class="chapter-body-save-footer">
    <span
      v-if="statusLabel"
      class="chapter-body-save-status"
      :class="{ 'chapter-body-save-status--error': autoSaveStatus === 'error' }"
      data-testid="chapter-body-save-status"
    >{{ statusLabel }}</span>
    <span v-else aria-hidden="true" />
    <button
      v-if="humanFirst"
      type="button"
      class="chapter-body-manual-save"
      data-testid="save-chapter-body-btn"
      :disabled="saving"
      @click="$emit('save')"
    >
      {{ saving ? '保存中…' : '手动保存' }}
    </button>
    <button
      v-else
      type="button"
      class="save-btn pixel-border"
      data-testid="save-chapter-body-btn"
      :disabled="saving"
      @click="$emit('save')"
    >
      {{ saving ? '保存中…' : '保存正文' }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  statusLabel: { type: String, default: '' },
  autoSaveStatus: { type: String, default: 'idle' },
  saving: { type: Boolean, default: false },
  humanFirst: { type: Boolean, default: false },
});

defineEmits(['save']);
</script>

<style scoped>
.chapter-body-manual-save {
  flex-shrink: 0;
  background: none;
  border: none;
  padding: 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.chapter-body-manual-save:hover:not(:disabled) {
  color: var(--color-accent);
}
.chapter-body-manual-save:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
