<!--
  PilotQueuePanel.vue — 批次优先级队列面板（后端 P2-QUEUE 的前端配合，只读）

  GET /studio/batch/queue 已按优先级（高优先在前、FIFO 平级）排序返回；
  此处仅展示排队中（尚未开始）的批次及其排队位置，无写操作。
  没有排队批次时不渲染面板。
-->
<template>
  <section v-if="queued.length" class="pilot-queue pilot-queue-panel panel-card queue-panel" data-testid="pilot-queue-panel">
    <h3 class="panel-title">排队中的批次</h3>
    <ol class="pilot-queue__list">
      <li
        v-for="(job, index) in queued"
        :key="job.job_id"
        class="pilot-queue__item"
        :data-testid="`pilot-queue-item-${job.job_id}`"
      >
        <span class="pilot-queue__pos">#{{ index + 1 }}</span>
        <span class="pilot-queue__range">{{ rangeLabel(job) }}</span>
        <span class="pilot-queue__mode">{{ job.mode }}</span>
        <span class="pilot-queue__time">{{ timeLabel(job) }}</span>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { StudioBatchJobSummaryDTO } from '@/api/studio';

const props = defineProps<{ queue: StudioBatchJobSummaryDTO[] }>();

const queued = computed(() => props.queue.filter((job) => job.status === 'queued'));

function pad(n: number): string {
  return String(n).padStart(3, '0');
}

function rangeLabel(job: StudioBatchJobSummaryDTO): string {
  return `ch${pad(job.start_chapter)}–ch${pad(job.end_chapter)}`;
}

function timeLabel(job: StudioBatchJobSummaryDTO): string {
  if (!job.started_at) return '';
  try {
    const d = new Date(job.started_at);
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString();
  } catch {
    return '';
  }
}
</script>

<style scoped>
.pilot-queue {
  margin-top: 0.75rem;
}
.pilot-queue__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.pilot-queue__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: var(--bg-elevated, var(--bg-muted));
  border-radius: var(--radius-sm, 6px);
  font-size: var(--text-sm, 13px);
}
.pilot-queue__pos {
  font-weight: 600;
  color: var(--accent, #b45309);
  min-width: 22px;
}
.pilot-queue__range {
  font-weight: 500;
  color: var(--text, #222);
}
.pilot-queue__mode {
  color: var(--text-tertiary, #888);
}
.pilot-queue__time {
  margin-left: auto;
  color: var(--text-tertiary, #888);
}
</style>
