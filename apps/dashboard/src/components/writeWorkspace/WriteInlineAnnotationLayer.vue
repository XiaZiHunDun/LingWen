<template>
  <div class="ws-annotation-layer annotation-layer" data-testid="annotation-layer">
    <button
      v-for="(a, idx) in annotations"
      :key="idx"
      type="button"
      class="ws-annotation-marker annotation-marker"
      :class="`is-${a.severity.toLowerCase()}`"
      :title="`${a.rule}: ${a.msg}`"
      data-testid="annotation-marker"
      @mouseenter="hovered = a"
      @mouseleave="hovered = null"
      @click="$emit('jumpToFix', a)"
    >
      {{ a.severity }}
    </button>
    <div v-if="hovered" class="ws-annotation-tooltip">
      <strong>{{ hovered.rule }}</strong>: {{ hovered.msg }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  annotations: { type: Array, required: true },
})

defineEmits(['jumpToFix'])

const hovered = ref(null)
</script>

<style scoped>
.ws-annotation-layer {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
}
.ws-annotation-marker {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  font-size: 0.625rem;
  font-weight: 700;
  cursor: pointer;
}
.ws-annotation-marker.is-p0 { background: var(--n-error-color); color: white; }
.ws-annotation-marker.is-p1 { background: var(--n-warning-color); color: white; }
.ws-annotation-tooltip {
  position: absolute;
  background: var(--n-tooltip-color);
  color: white;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  max-width: 240px;
}
</style>