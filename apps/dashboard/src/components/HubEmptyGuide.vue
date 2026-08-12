<!--
  HubEmptyGuide.vue — 紧凑空状态（主 CTA 突出）
-->
<template>
  <section
    class="hub-empty-guide pixel-border"
    :data-testid="testId"
  >
    <div class="hub-empty-guide__copy">
      <p class="hub-empty-guide__title">{{ title }}</p>
      <p v-if="hint" class="hub-empty-guide__hint">{{ hint }}</p>
    </div>
    <div v-if="primaryLabel || secondaryLabel" class="hub-empty-guide__actions">
      <button
        v-if="primaryLabel"
        type="button"
        class="hub-empty-guide__primary pixel-border"
        :data-testid="primaryTestId"
        @click="$emit('primary')"
      >
        {{ primaryLabel }}
      </button>
      <button
        v-if="secondaryLabel"
        type="button"
        class="hub-empty-guide__secondary pixel-border"
        :data-testid="secondaryTestId"
        @click="$emit('secondary')"
      >
        {{ secondaryLabel }}
      </button>
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  hint: { type: String, default: '' },
  primaryLabel: { type: String, default: '' },
  secondaryLabel: { type: String, default: '' },
  primaryTestId: { type: String, default: 'hub-empty-primary' },
  secondaryTestId: { type: String, default: 'hub-empty-secondary' },
  testId: { type: String, default: 'hub-empty-guide' },
});

defineEmits(['primary', 'secondary']);
</script>

<style scoped>
.hub-empty-guide {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md);
  margin: 0 var(--space-md) var(--space-sm);
  background: var(--bg-secondary);
}

.hub-empty-guide__copy {
  flex: 1;
  min-width: min(280px, 100%);
}

.hub-empty-guide__title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: 600;
}

.hub-empty-guide__hint {
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
  color: var(--text-muted, var(--color-text-dim));
  line-height: var(--leading-relaxed);
}

.hub-empty-guide__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
}

.hub-empty-guide__primary {
  font-size: var(--text-sm);
  font-weight: 600;
  padding: 10px 16px;
  background: var(--color-accent);
  color: #fff;
  cursor: pointer;
  border: 3px solid var(--border-color);
}

.hub-empty-guide__secondary {
  font-size: var(--text-sm);
  padding: 8px 14px;
  background: var(--bg-primary);
  cursor: pointer;
}
</style>
