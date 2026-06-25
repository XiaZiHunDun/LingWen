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
      class="scale-btn pixel-border"
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
  gap: 4px;
}

.scale-btn {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  padding: 4px 8px;
  background: var(--bg-primary);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.scale-btn--active {
  background: var(--color-accent);
  color: white;
}
</style>
