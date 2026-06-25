<template>
  <span
    v-if="meta.label"
    class="creation-mode-hint pixel-border"
    data-testid="creation-mode-hint"
    :title="meta.audience"
  >
    <strong>{{ meta.label }}</strong>
    <span v-if="meta.tagline" class="hint-sep">·</span>
    <span class="hint-tagline">{{ meta.tagline }}</span>
  </span>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { fetchStudioSummary } from '../api/index.js';
import { creationModeMeta } from '../utils/creationModeHint.js';
import { useStudioProject } from '../composables/useStudioProject.js';

const props = defineProps({
  mode: { type: String, default: '' },
});

const { summary } = useStudioProject();
const localMode = ref('');

onMounted(() => {
  if (!props.mode && !summary.value) {
    fetchStudioSummary()
      .then((s) => { localMode.value = s?.creation_mode || ''; })
      .catch(() => {});
  }
});

const meta = computed(() => {
  const mode = props.mode || summary.value?.creation_mode || localMode.value;
  return creationModeMeta(mode);
});
</script>

<style scoped>
.creation-mode-hint {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  background: var(--bg-primary);
  max-width: 420px;
}

.hint-sep {
  opacity: 0.5;
}

.hint-tagline {
  color: var(--color-text-dim);
  font-weight: 400;
}
</style>
