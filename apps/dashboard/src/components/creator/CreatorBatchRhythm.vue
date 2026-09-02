<!--
  CreatorBatchRhythm.vue — 推进模式「批改节奏带」（REQ-001 切片 C，只读）

  复用 usePilotBatch 读取当前批改批次（SSE 实时 + 场景重放）的完成进度，
  把批次章节范围渲染成一条「节奏带」：
  - 每章一格：已改定（模式色）、未开始（灰）、越序改定（偏差高亮）
  - 章节偏差：前序章节尚未改定时就完成 > 标记为偏差并给出提示

  本组件只读：不发起写操作，仅挂载时 fetch 一次当前活跃批次用于初始化。
-->
<template>
  <section class="batch-rhythm creator-batch-rhythm" data-testid="creator-batch-rhythm">
    <h2 class="batch-rhythm__title">批改节奏带</h2>

    <p v-if="!hasBatch" class="batch-rhythm__empty creator-batch-rhythm-empty" data-testid="creator-batch-rhythm-empty">
      当前无批改批次；发起批量生成后可在此查看章节完成节奏。
    </p>

    <template v-else>
      <div class="batch-rhythm__head">
        <span class="batch-rhythm__status" :class="`batch-rhythm__status--${statusTone}`">
          {{ statusLabel }}
        </span>
        <span class="batch-rhythm__range">ch{{ pad(range.start) }}–ch{{ pad(range.end) }}</span>
        <span class="batch-rhythm__progress creator-batch-rhythm-progress" data-testid="creator-batch-rhythm-progress">
          {{ completedCount }}/{{ range.total }}
          <em v-if="deviations.length">· {{ deviations.length }} 处偏差</em>
        </span>
      </div>

      <div class="batch-rhythm__band creator-batch-rhythm-band" data-testid="creator-batch-rhythm-band">
        <span
          v-for="cell in band"
          :key="cell.num"
          class="batch-rhythm__cell"
          :class="{ 'is-done': cell.state === 'done', 'is-deviating': cell.state === 'deviating' }"
          :title="cell.title"
          :data-testid="`creator-batch-rhythm-cell-${cell.num}`"
          :data-state="cell.state"
        >
          {{ pad(cell.num) }}
        </span>
      </div>

      <div class="batch-rhythm__bar">
        <div class="batch-rhythm__bar-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>

      <div v-if="deviations.length" class="batch-rhythm__deviations creator-batch-rhythm-deviations" data-testid="creator-batch-rhythm-deviations">
        <h3 class="batch-rhythm__subtitle">章节偏差</h3>
        <p
          v-for="d in deviations"
          :key="d.num"
          class="batch-rhythm__deviation"
          :data-testid="`creator-batch-rhythm-deviation-${d.num}`"
        >
          {{ d.text }}
        </p>
      </div>

      <p v-if="!isJobActive" class="batch-rhythm__hint">
        当前批次已结束；此处保留最近批次的完成记录。
      </p>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { usePilotBatch } from '@/composables/usePilotBatch';
import {
  computeBatchRange,
  computeCompletedNums,
  computeBatchDeviations,
  computeBatchDeviatingNums,
  buildBatchBand,
  padChapter as pad,
} from '@/utils/batchDeviation';

const pilot = usePilotBatch();
const activeJob = pilot.activeJob;
const chapterEvents = pilot.chapterEvents;
const isJobActive = pilot.isJobActive;

const hasBatch = computed(() => !!activeJob.value);

const range = computed(() => computeBatchRange(activeJob.value));

const completedSet = computed(() => computeCompletedNums(chapterEvents.value));

// 越序偏差：某章已完成，但其前序（范围内、编号更小）章节仍未完成。
const deviations = computed(() =>
  computeBatchDeviations(range.value.start, range.value.end, completedSet.value),
);

const deviatingNums = computed(() => computeBatchDeviatingNums(deviations.value));

const band = computed(() =>
  buildBatchBand(range.value.start, range.value.end, completedSet.value, deviatingNums.value),
);

const completedCount = computed(() => {
  const { start, end } = range.value;
  let count = 0;
  for (const num of completedSet.value) {
    if (num >= start && num <= end) count += 1;
  }
  return count;
});

const progressPercent = computed(() => {
  const { total } = range.value;
  if (!total) return 0;
  return Math.round((completedCount.value / total) * 100);
});

const statusLabel = computed(() => {
  const s = activeJob.value?.status ?? '';
  const labels: Record<string, string> = {
    running: '批改中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  };
  return labels[s] ?? (s ? s : '空闲');
});

const statusTone = computed(() => activeJob.value?.status ?? 'idle');

onMounted(() => {
  pilot.refreshActive();
});
</script>

<style scoped>
.batch-rhythm {
  padding: 12px;
  background: var(--bg-muted);
  border-radius: var(--radius-md);
}

.batch-rhythm__title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 12px 0;
}

.batch-rhythm__empty {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

.batch-rhythm__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.batch-rhythm__status {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  background: var(--bg-primary);
  color: var(--color-text-secondary);
}

.batch-rhythm__status--running {
  color: var(--color-accent);
}

.batch-rhythm__status--completed {
  color: #16a34a;
}

.batch-rhythm__status--failed,
.batch-rhythm__status--cancelled {
  color: #dc2626;
}

.batch-rhythm__range {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.batch-rhythm__progress {
  margin-left: auto;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.batch-rhythm__progress em {
  font-style: normal;
  color: #d97706;
}

.batch-rhythm__band {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.batch-rhythm__cell {
  min-width: 30px;
  text-align: center;
  font-size: var(--text-xs);
  padding: 4px 6px;
  border-radius: var(--radius-xs);
  background: var(--bg-primary);
  color: var(--color-text-tertiary);
  border: 1px solid var(--border-color);
}

.batch-rhythm__cell.is-done {
  background: var(--color-accent-soft, var(--bg-elevated));
  color: var(--color-accent);
  border-color: transparent;
}

.batch-rhythm__cell.is-deviating {
  background: #fef3c7;
  color: #b45309;
  border-color: #f59e0b;
}

.batch-rhythm__bar {
  height: 4px;
  background: var(--bg-primary);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 10px;
}

.batch-rhythm__bar-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.3s ease;
}

.batch-rhythm__subtitle {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-tertiary);
  margin: 0 0 6px 0;
}

.batch-rhythm__deviations {
  padding: 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-xs);
  margin-bottom: 8px;
}

.batch-rhythm__deviation {
  font-size: var(--text-xs);
  color: #b45309;
  margin: 0 0 4px 0;
}

.batch-rhythm__deviation:last-child {
  margin-bottom: 0;
}

.batch-rhythm__hint {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}
</style>