<!--
  CreatorAgentAnnotations.vue — Agent 透镜标注（编辑/审稿等）
-->
<template>
  <div
    v-if="annotations.length"
    class="agent-annotations pixel-border"
    :data-testid="mainBar ? 'write-agent-annotations-main' : 'write-agent-annotations'"
  >
    <p class="agent-annotations__title">
      透镜标注
      <span v-if="lensLabel" class="agent-annotations__lens">· {{ lensLabel }}</span>
    </p>
    <ul class="agent-annotations__list">
      <li
        v-for="ann in annotations"
        :key="ann.id"
        class="agent-annotations__item"
        :class="`agent-annotations__item--${ann.level || 'info'}`"
        :data-testid="`agent-annotation-${ann.id}`"
      >
        <button
          type="button"
          class="agent-annotations__btn"
          @click="$emit('focus', ann)"
        >
          <span v-if="ann.paragraph" class="agent-annotations__para">¶{{ ann.paragraph }}</span>
          {{ ann.text }}
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { AGENT_LENS_MODES } from '../../config/creatorPanelMatrix.js';

const props = defineProps({
  annotations: { type: Array, default: () => [] },
  lens: { type: String, default: 'author' },
  /** human-first 主区展示，与 advanced-tools 内条区分 testid */
  mainBar: { type: Boolean, default: false },
});

defineEmits(['focus']);

const lensLabel = computed(() => {
  const found = AGENT_LENS_MODES.find((m) => m.id === props.lens);
  return found?.label || '';
});
</script>

<style scoped>
.agent-annotations {
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-xs);
  margin-bottom: var(--space-xs);
}
.agent-annotations__title {
  font-weight: 600;
  margin: 0 0 var(--space-xs);
}
.agent-annotations__lens {
  font-weight: 400;
  color: var(--color-text-dim);
}
.agent-annotations__list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.agent-annotations__item {
  border-bottom: 1px solid var(--border-color);
}
.agent-annotations__item--warn { color: #a60; }
.agent-annotations__item--error { color: var(--color-danger); }
.agent-annotations__item--info { color: var(--color-text-dim); }
.agent-annotations__btn {
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  padding: 4px 0;
  cursor: pointer;
  font: inherit;
  color: inherit;
}
.agent-annotations__btn:hover {
  text-decoration: underline;
}
.agent-annotations__para {
  display: inline-block;
  min-width: 1.5em;
  margin-right: 4px;
  opacity: 0.7;
}
</style>
