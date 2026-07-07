<!--
  CreatorLightValidationBar.vue — 写中轻量校验条（非阻断）
-->
<template>
  <div
    class="write-light-validation"
    :class="`write-light-validation--${summary.status}`"
    data-testid="write-light-validation-bar"
  >
    <div class="write-light-validation__head">
      <span class="write-light-validation__label">
        {{ running ? '校验中…' : summary.label }}
      </span>
      <span v-if="issues.length" class="meta-line">{{ issues.length }} 条</span>
    </div>
    <ul v-if="issues.length" class="write-light-validation__list">
      <li
        v-for="issue in issues"
        :key="issue.id"
        class="write-light-validation__item"
        :class="`write-light-validation__item--${issue.level}`"
      >
        <button
          type="button"
          class="write-light-validation__pill"
          :data-testid="`light-validation-${issue.rule}`"
          @click="$emit('focus', issue)"
        >
          {{ issue.label }}
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { summarizeLightValidation } from '../../utils/creatorLightValidationUtils.js';

const props = defineProps({
  issues: { type: Array, default: () => [] },
  running: { type: Boolean, default: false },
});

defineEmits(['focus']);

const summary = computed(() => summarizeLightValidation(props.issues));
</script>

<style scoped>
.write-light-validation {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  font-size: var(--text-xs);
}

.write-light-validation--ok {
  border-color: color-mix(in srgb, var(--color-accent) 35%, var(--border-color));
}

.write-light-validation--warn {
  border-color: color-mix(in srgb, var(--color-warning) 45%, var(--border-color));
}

.write-light-validation__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-sm);
}

.write-light-validation__label {
  font-weight: 600;
}

.write-light-validation__list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.write-light-validation__pill {
  border: 1px dashed var(--border-color);
  background: var(--bg-primary);
  border-radius: 999px;
  padding: 2px 8px;
  font-size: var(--text-xs);
  cursor: pointer;
}

.write-light-validation__item--warn .write-light-validation__pill {
  border-color: color-mix(in srgb, var(--color-warning) 55%, var(--border-color));
}

.meta-line {
  margin: 0;
  color: var(--color-text-dim);
}
</style>
