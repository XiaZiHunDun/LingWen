<!--
  CreatorDeviationFinalize.vue — 推进模式「差异收尾」（REQ-001 切片 E）

  在批次节奏带之下，把越序改定的差异章整理成可操作的收尾清单：
  - 每条列出差异章 + 说明 + 「标记已复核」开关
  - 复核状态按批次（job_id）持久化到 localStorage
  - 全部复核后显示「差异已收尾」并支持重置
  复用与节奏带同源的批次偏差推导（utils/batchDeviation）。
-->
<template>
  <section class="deviation-finalize creator-deviation-finalize" data-testid="creator-deviation-finalize">
    <h2 class="deviation-finalize__title">差异收尾</h2>

    <p v-if="range.total === 0" class="deviation-finalize__empty creator-deviation-finalize-empty" data-testid="creator-deviation-finalize-empty">
      当前无批次，无待收尾差异。
    </p>

    <template v-else>
      <p v-if="!deviations.length" class="deviation-finalize__clean creator-deviation-finalize-clean" data-testid="creator-deviation-finalize-clean">
        ✓ 本批次无越序差异，无需收尾。
      </p>

      <template v-else>
        <div class="deviation-finalize__head">
          <span class="deviation-finalize__progress creator-deviation-finalize-progress" data-testid="creator-deviation-finalize-progress">
            {{ reviewedCount }}/{{ deviations.length }} 已复核
          </span>
          <button
            type="button"
            class="deviation-finalize__reset creator-deviation-finalize-reset"
            data-testid="creator-deviation-finalize-reset"
            @click="reset"
          >
            重置
          </button>
        </div>

        <ul class="deviation-finalize__list creator-deviation-finalize-list" data-testid="creator-deviation-finalize-list">
          <li
            v-for="d in deviations"
            :key="d.num"
            class="deviation-finalize__item"
            :class="{ 'is-reviewed': isReviewed(d.num) }"
          >
            <span class="deviation-finalize__chapter">ch{{ pad(d.num) }}</span>
            <span class="deviation-finalize__text">{{ d.text }}</span>
            <button
              type="button"
              class="deviation-finalize__toggle"
              :class="{ 'is-reviewed': isReviewed(d.num) }"
              :data-testid="`creator-deviation-finalize-toggle-${d.num}`"
              @click="toggle(d.num)"
            >
              {{ isReviewed(d.num) ? '已复核 ✓' : '标记已复核' }}
            </button>
          </li>
        </ul>

        <p v-if="allReviewed" class="deviation-finalize__done creator-deviation-finalize-done" data-testid="creator-deviation-finalize-done">
          🎉 全部差异已收尾
        </p>
      </template>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { usePilotBatch } from '@/composables/usePilotBatch';
import {
  computeBatchRange,
  computeCompletedNums,
  computeBatchDeviations,
  padChapter as pad,
} from '@/utils/batchDeviation';

const STORAGE_PREFIX = 'creator-deviation-review';

const pilot = usePilotBatch();
const activeJob = pilot.activeJob;
const chapterEvents = pilot.chapterEvents;

const range = computed(() => computeBatchRange(activeJob.value));
const completedSet = computed(() => computeCompletedNums(chapterEvents.value));
const deviations = computed(() =>
  computeBatchDeviations(range.value.start, range.value.end, completedSet.value),
);

const reviewed = ref<Set<number>>(new Set());

function storageKey(): string {
  return `${STORAGE_PREFIX}:${activeJob.value?.job_id ?? 'none'}`;
}

function loadReviewed(): Set<number> {
  try {
    const raw = window.localStorage.getItem(storageKey());
    if (!raw) return new Set();
    const parsed = JSON.parse(raw) as unknown;
    return new Set(Array.isArray(parsed) ? parsed.filter((n): n is number => typeof n === 'number') : []);
  } catch {
    return new Set();
  }
}

function persistReviewed(): void {
  try {
    window.localStorage.setItem(storageKey(), JSON.stringify([...reviewed.value]));
  } catch {
    /* localStorage 不可用时保持内存态 */
  }
}

// 活跃批次变化时重载该批次的复核状态。
watch(
  () => activeJob.value?.job_id,
  () => {
    reviewed.value = loadReviewed();
  },
  { immediate: true },
);

function isReviewed(num: number): boolean {
  return reviewed.value.has(num);
}

function toggle(num: number): void {
  const next = new Set(reviewed.value);
  if (next.has(num)) {
    next.delete(num);
  } else {
    next.add(num);
  }
  reviewed.value = next;
  persistReviewed();
}

function reset(): void {
  reviewed.value = new Set();
  persistReviewed();
}

const reviewedCount = computed(
  () => deviations.value.filter((d) => reviewed.value.has(d.num)).length,
);

const allReviewed = computed(
  () => deviations.value.length > 0 && reviewedCount.value === deviations.value.length,
);
</script>

<style scoped>
.deviation-finalize {
  padding: 12px;
  background: var(--bg-muted);
  border-radius: var(--radius-md);
}

.deviation-finalize__title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 10px 0;
}

.deviation-finalize__empty,
.deviation-finalize__clean,
.deviation-finalize__done {
  font-size: var(--text-xs);
  margin: 0;
}

.deviation-finalize__empty,
.deviation-finalize__clean {
  color: var(--color-text-tertiary);
}

.deviation-finalize__done {
  margin-top: 8px;
  color: #16a34a;
  font-weight: 500;
}

.deviation-finalize__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.deviation-finalize__progress {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.deviation-finalize__reset {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-xs);
  background: var(--bg-primary);
  color: var(--color-text-tertiary);
  cursor: pointer;
}

.deviation-finalize__reset:hover {
  color: var(--color-text);
  background: var(--bg-elevated);
}

.deviation-finalize__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.deviation-finalize__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-xs);
}

.deviation-finalize__item.is-reviewed {
  background: var(--bg-primary);
  border-color: var(--border-color);
}

.deviation-finalize__chapter {
  flex: none;
  font-size: var(--text-xs);
  font-weight: 600;
  color: #b45309;
}

.deviation-finalize__text {
  flex: 1;
  font-size: var(--text-xs);
  color: #92400e;
}

.deviation-finalize__toggle {
  flex: none;
  font-size: var(--text-xs);
  padding: 3px 8px;
  border: var(--border-width) solid #f59e0b;
  border-radius: var(--radius-xs);
  background: #fff;
  color: #b45309;
  cursor: pointer;
}

.deviation-finalize__toggle.is-reviewed {
  border-color: var(--border-color);
  background: var(--bg-primary);
  color: #16a34a;
}
</style>
