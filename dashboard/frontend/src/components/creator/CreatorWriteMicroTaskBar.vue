<!--
  CreatorWriteMicroTaskBar.vue — 章内微任务条（再写 N 字）
-->
<template>
  <div class="write-micro-task" data-testid="write-micro-task-bar">
    <div class="write-micro-task__row">
      <span class="write-micro-task__label">
        <template v-if="progress.met">本章字数已达标</template>
        <template v-else>再写 {{ progress.remaining }} 字</template>
      </span>
      <span class="write-micro-task__meta meta-line">
        {{ progress.current }} / {{ progress.goal }} 字
      </span>
    </div>
    <div
      class="write-micro-task__track"
      role="progressbar"
      :aria-valuenow="progress.progress"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="progress.met ? '本章字数已达标' : `再写 ${progress.remaining} 字`"
    >
      <div
        class="write-micro-task__fill"
        :style="{ width: `${progress.progress}%` }"
        data-testid="write-micro-task-fill"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { buildMicroTaskProgress } from '../../utils/creatorMicroTaskUtils.js';

const props = defineProps({
  draft: { type: String, default: '' },
  creationMode: { type: String, default: 'companion' },
  goal: { type: Number, default: 0 },
});

const progress = computed(() =>
  buildMicroTaskProgress({
    draft: props.draft,
    creationMode: props.creationMode,
    goal: props.goal,
  }),
);
</script>

<style scoped>
.write-micro-task {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  border-radius: 8px;
  font-size: var(--text-xs);
}

.write-micro-task__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-sm);
}

.write-micro-task__label {
  font-weight: 600;
  color: var(--color-text);
}

.write-micro-task__track {
  height: 6px;
  border-radius: 999px;
  background: var(--bg-muted);
  overflow: hidden;
}

.write-micro-task__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--color-accent-soft), var(--color-accent));
  transition: width 0.2s ease;
}
</style>
