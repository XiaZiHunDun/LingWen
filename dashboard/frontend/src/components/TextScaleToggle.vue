<template>
  <div
    class="text-scale-toggle"
    role="group"
    aria-label="界面字号"
    data-testid="text-scale-toggle"
  >
    <button
      v-for="opt in TEXT_SCALE_OPTIONS"
      :key="opt.id"
      type="button"
      class="scale-btn"
      :class="{ 'scale-btn--active': activeScale === opt.id }"
      :data-testid="`text-scale-${opt.id}`"
      :aria-pressed="activeScale === opt.id"
      @click="pick(opt.id)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import {
  TEXT_SCALE_OPTIONS,
  getStoredTextScale,
  setTextScale,
} from '../utils/textScale.js';

const activeScale = ref('normal');

onMounted(() => {
  activeScale.value = getStoredTextScale();
});

function pick(scale) {
  activeScale.value = setTextScale(scale);
}
</script>

<style scoped>
.text-scale-toggle {
  display: inline-flex;
  gap: 0;
  padding: 3px;
  background: var(--bg-muted);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
}

.scale-btn {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  padding: 5px 10px;
  background: transparent;
  border: none;
  border-radius: calc(var(--radius-sm) - 2px);
  cursor: pointer;
  color: var(--color-text-dim);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.scale-btn:hover:not(.scale-btn--active) {
  background: var(--bg-elevated);
  color: var(--color-text);
}

.scale-btn--active {
  background: var(--bg-elevated);
  color: var(--color-accent);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}
</style>
