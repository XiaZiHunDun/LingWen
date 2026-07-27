<template>
  <details class="creation-mode-hint-compact creation-mode-hint" data-testid="creation-mode-hint">
    <summary :title="meta.audience">{{ meta.label }}</summary>
    <p v-if="meta.tagline" class="creation-mode-hint-compact__body">
      {{ meta.tagline }}
    </p>
  </details>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { fetchStudioSummary } from '../api/index.js';
import { creationModeMeta } from '../utils/creationModeHint.js';
import { useStudioProject } from '../composables/index.js';
import { logger } from '../utils/logger.js';

const props = defineProps({
  mode: { type: String, default: '' },
});

const { summary } = useStudioProject();
const localMode = ref('');

onMounted(() => {
  if (!props.mode && !summary) {
    fetchStudioSummary()
      .then((s) => { localMode.value = s?.creation_mode || ''; })
      .catch((err) => { logger.warn('fetchStudioSummary failed in CreationModeHint', err); });
  }
});

const meta = computed(() => {
  const mode = props.mode || summary?.creation_mode || localMode.value;
  return creationModeMeta(mode);
});
</script>
