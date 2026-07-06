<template>
  <div class="creator-pulse-intro" :class="{ 'creator-pulse-intro--tabbed': tabbed }">
    <h2 v-if="!tabbed" class="column-title">脉络</h2>
    <p v-if="!tabbed" class="column-hint">
      写作进度 · 卷纲与偏离
    </p>
    <p v-else-if="!showEmptyGuide" class="column-hint column-hint--tabbed">
      写作进度与卷纲偏离
    </p>
    <div
      v-if="showEmptyGuide"
      class="pulse-empty-guide pixel-border"
      data-testid="pulse-empty-guide"
    >
      <p class="subsection-title">暂无脉络数据</p>
      <p class="meta-line">
        陪伴模式以逐章写作为主。写完 ch001 后，偏离项会出现在这里；也可在下方添加卷纲规划多章节奏。
      </p>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="pulse-empty-go-write-btn"
        @click="$emit('go-write')"
      >
        回到写作
      </button>
    </div>
    <div v-if="overview" class="progress-block" :class="{ 'progress-block--tabbed': tabbed }">
      <div class="progress-block__row">
        <p class="progress-text">
          已写 <strong>{{ overview.chapters_written }}</strong> / {{ overview.max_chapter }} 章
          <span class="progress-text__pct">（{{ overview.coverage_pct }}%）</span>
        </p>
        <p v-if="overview.chapters_written === 0" class="progress-hint meta-line" data-testid="pulse-progress-hint">
          还没开始写第一章
        </p>
      </div>
      <div class="progress-bar pixel-border" role="progressbar" :aria-valuenow="overview.coverage_pct" aria-valuemin="0" aria-valuemax="100">
        <div
          class="progress-fill"
          :class="progressFillClass"
          :style="{ width: `${progressBarWidth}%` }"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  overview: { type: Object, default: null },
  showEmptyGuide: { type: Boolean, default: false },
  /** Tab 模式下顶栏已有「脉络」标签，隐藏重复栏标题 */
  tabbed: { type: Boolean, default: false },
});

defineEmits(['go-write']);

const progressFillClass = computed(() => {
  const pct = props.overview?.coverage_pct ?? 0;
  if (pct >= 80) return 'progress-fill--high';
  if (pct >= 40) return 'progress-fill--mid';
  return 'progress-fill--low';
});

const progressBarWidth = computed(() => {
  const pct = props.overview?.coverage_pct ?? 0;
  if (pct <= 0) return 3;
  return Math.min(100, pct);
});
</script>

<style scoped>
.creator-pulse-intro--tabbed .progress-block {
  margin-bottom: 0;
}

.column-hint--tabbed {
  margin: 0 0 var(--space-xs);
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.progress-block--tabbed {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.progress-block__row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-xs);
}

.progress-text__pct {
  color: var(--color-text-dim);
  font-weight: 500;
}

.pulse-empty-guide {
  margin-bottom: var(--space-sm);
  padding: var(--space-md);
}

.pulse-empty-guide .meta-line {
  margin: var(--space-xs) 0 var(--space-sm);
}

.progress-block {
  margin-bottom: var(--space-sm);
}

.progress-text {
  font-size: var(--text-sm);
  margin-bottom: var(--space-xs);
}

.progress-hint {
  margin: 0 0 var(--space-xs);
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.progress-bar {
  height: 12px;
  background: var(--color-accent-soft, var(--bg-muted));
  overflow: hidden;
  border-radius: var(--radius-sm);
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.25s ease;
}

.progress-fill--low {
  background: linear-gradient(90deg, var(--color-warning, #c9a227), var(--color-accent));
}

.progress-fill--mid {
  background: linear-gradient(90deg, var(--color-accent), var(--color-success, #2e7d5a));
}

.progress-fill--high {
  background: linear-gradient(90deg, var(--color-success, #2e7d5a), var(--color-success, #2e7d5a));
}
</style>
