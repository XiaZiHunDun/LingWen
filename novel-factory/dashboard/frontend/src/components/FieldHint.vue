<!--
  FieldHint.vue — 术语悬浮释义（P1）
-->
<template>
  <span class="field-hint" :data-testid="testId || undefined">
    <span class="field-hint__label"><slot /></span>
    <button
      type="button"
      class="field-hint__trigger"
      :aria-label="`${label}说明`"
      :title="hint"
      :data-testid="testId ? `${testId}-trigger` : undefined"
    >
      ?
    </button>
  </span>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  hint: { type: String, required: true },
  testId: { type: String, default: '' },
});
</script>

<style scoped>
.field-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.field-hint__label {
  font: inherit;
}
.field-hint__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  color: var(--color-text-dim);
  background: var(--bg-muted);
  border: none;
  border-radius: 50%;
  cursor: help;
}
.field-hint__trigger:hover {
  color: var(--color-accent);
  background: var(--color-accent-soft);
}
</style>
