<!--
  PilotLivePanel.vue — 实时状态：状态徽标 + 章节范围 + ETA + log tail + Cancel（P1）
-->
<template>
  <section class="pilot-live-panel pixel-card" data-testid="pilot-live-panel">
    <h2 class="section-title">实时状态</h2>
    <p v-if="!activeJob" class="pilot-live-empty empty-msg" data-testid="pilot-live-empty">无正在运行的 batch</p>
    <div v-else class="live-content">
      <div class="status-row">
        <span class="status-label">状态:</span>
        <strong class="pilot-status" :class="`job-status-${statusColor}`" data-testid="pilot-status">{{ activeJob.status }}</strong>
        <span class="chapter-range">{{ chapterRange }}</span>
        <span class="budget">${{ activeJob.budget_usd }}</span>
        <span v-if="activeJob.pid" class="pid">pid: {{ activeJob.pid }}</span>
      </div>
      <div v-if="eventTypeOptions?.length" class="event-filter">
        <span class="event-filter-label">事件过滤:</span>
        <div class="event-filter-chips" data-testid="pilot-event-filter">
          <button
            v-for="opt in eventTypeOptions"
            :key="opt.value"
            type="button"
            class="filter-chip pilot-event-filter-chip"
            :class="{ 'is-active': selectedEventTypes?.includes(opt.value) }"
            :data-event-type="opt.value"
            @click="emit('toggle-event-type', opt.value)"
          >{{ opt.label }}</button>
        </div>
      </div>
      <div class="eta-row">
        <span class="eta-label">预计剩余:</span>
        <span class="eta-value pilot-eta" data-testid="pilot-eta">{{ etaDisplay }}</span>
      </div>
      <ul v-if="recentChapters.length" class="chapter-events pilot-chapter-events" data-testid="pilot-chapter-events">
        <li
          v-for="item in recentChapters"
          :key="`${item.chapter_num}-${item.receivedAt}`"
          class="chapter-event-item-wrap"
        >
          <button
            type="button"
            class="chapter-event-item"
            :data-testid="`pilot-preview-chapter-${item.chapter_num}`"
            :title="`预览 ch${String(item.chapter_num).padStart(3, '0')}`"
            @click="emit('open-preview', item.chapter_num)"
          >
            已完成 <strong>ch{{ String(item.chapter_num).padStart(3, '0') }}</strong>
          </button>
        </li>
      </ul>
      <pre v-if="activeJob.log_tail" class="log-tail pilot-log-tail" data-testid="pilot-log-tail">{{ activeJob.log_tail }}</pre>
      <div class="actions-row">
        <button v-if="activeJob.status === 'running'" type="button" class="cancel-btn pilot-cancel-btn pixel-border" data-testid="pilot-cancel-btn" :disabled="cancelLoading" @click="emit('request-cancel', activeJob.job_id)">
          {{ cancelLoading ? '取消中…' : 'Cancel' }}
        </button>
      </div>
    </div>

    <div
      v-if="previewOpen"
      class="preview-drawer"
      data-testid="pilot-preview-drawer"
      @click.self="emit('close-preview')"
    >
      <div class="preview-drawer__panel">
        <header class="preview-drawer__header">
          <h3 class="preview-drawer__title">章节预览 ch{{ String(previewChapter ?? 0).padStart(3, '0') }}</h3>
          <button type="button" class="preview-drawer__close" data-testid="pilot-preview-close" @click="emit('close-preview')">×</button>
        </header>
        <div class="preview-drawer__body">
          <p v-if="previewLoading" class="preview-drawer__hint" data-testid="pilot-preview-loading">加载中…</p>
          <p v-else-if="previewError" class="preview-drawer__error" data-testid="pilot-preview-error">{{ previewError }}</p>
          <div v-else-if="previewData" class="preview-drawer__content" data-testid="pilot-preview-content">
            <h4 class="preview-drawer__subtitle">大纲</h4>
            <p v-text="previewData.outline || '（暂无大纲）'" class="preview-drawer__text" />
            <h4 class="preview-drawer__subtitle">正文</h4>
            <p v-text="previewData.body ? previewData.body.trim().slice(0, 800) : '（暂无正文）'" class="preview-drawer__text" />
          </div>
          <p v-else class="preview-drawer__hint" data-testid="pilot-preview-empty">打开章节以查看预览</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { BatchEventType } from '@/composables/useBatchEventStream';
import type { CreatorChapterPreview } from '@lingwen/dashboard-contracts/shared';
import type { StudioBatchJobResponseDTO } from '@/api/studio';

// 直接复用后端 DTO,避免本地接口与契约漂移(Phase 25.3 类型债清理)
type ActiveJob = StudioBatchJobResponseDTO;

interface EventTypeOption {
  value: BatchEventType;
  label: string;
}

const props = defineProps<{
  activeJob: ActiveJob | null;
  etaSeconds: number | null;
  cancelLoading: boolean;
  chapterEvents?:
    | Array<{ chapter_num: number; receivedAt: string }>
    | null;
  eventTypeOptions?: ReadonlyArray<EventTypeOption>;
  selectedEventTypes?: BatchEventType[];
  previewChapter?: number | null;
  previewData?: CreatorChapterPreview | null;
  previewLoading?: boolean;
  previewError?: string | null;
}>();

const emit = defineEmits<{
  'request-cancel': [jobId: string];
  'toggle-event-type': [value: BatchEventType];
  'open-preview': [chapterNum: number];
  'close-preview': [];
}>();

/** Drawer is open whenever a chapter has been selected for preview. */
const previewOpen = computed(() => props.previewChapter != null);

/** Most recent 5 chapter_completed entries for a compact live list. */
const recentChapters = computed(() => props.chapterEvents?.slice(-5) ?? []);

const statusColor = computed(() => {
  if (!props.activeJob) return 'unknown';
  return props.activeJob.status;
});

const etaDisplay = computed(() => {
  if (props.etaSeconds === null) return '等待首个 chapter 完成…';
  const minutes = Math.floor(props.etaSeconds / 60);
  const seconds = Math.round(props.etaSeconds % 60);
  if (minutes >= 1) return `约 ${minutes}分${seconds}秒`;
  return `约 ${seconds}秒`;
});

const chapterRange = computed(() => {
  if (!props.activeJob) return '';
  return `ch${String(props.activeJob.start_chapter).padStart(3, '0')}–ch${String(props.activeJob.end_chapter).padStart(3, '0')}`;
});
</script>

<style scoped>
.pilot-live-panel { padding: 1rem; margin-bottom: 1rem; }
.status-row { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.5rem; }
.job-status-running { color: var(--success, #2c7a2c); font-weight: 600; }
.job-status-completed { color: var(--info, #2c6cb0); font-weight: 600; }
.job-status-failed, .job-status-cancelled { color: var(--error, #c33); font-weight: 600; }
.eta-row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
.event-filter { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.5rem; }
.event-filter-label { color: var(--muted, #888); font-size: 0.8rem; }
.event-filter-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.filter-chip { font-size: 0.78rem; padding: 0.15rem 0.6rem; border-radius: 12px; cursor: pointer; background: transparent; color: var(--muted, #888); border: 1px solid var(--muted, #aaa); }
.filter-chip.is-active { background: var(--info, #2c6cb0); color: #fff; border-color: var(--info, #2c6cb0); }
.chapter-events { list-style: none; margin: 0 0 0.5rem; padding: 0; display: flex; flex-wrap: wrap; gap: 0.4rem; }
.chapter-event-item-wrap { list-style: none; }
.chapter-event-item { font-size: 0.8rem; background: var(--info-bg, #eef); color: var(--info, #2c6cb0); padding: 0.15rem 0.5rem; border-radius: 4px; border: 1px solid transparent; cursor: pointer; font-family: inherit; }
.chapter-event-item:hover { border-color: var(--info, #2c6cb0); }
.log-tail { background: var(--code-bg, #1e1e1e); color: var(--code-f, #ddd); padding: 0.5rem; border-radius: 4px; max-height: 200px; overflow-y: auto; font-size: 0.85rem; }
.empty-msg { color: var(--muted, #888); font-style: italic; }
.cancel-btn { padding: 0.4rem 0.8rem; cursor: pointer; background: var(--error-bg, #fee); color: var(--error, #c33); border-color: var(--error, #c33); }
.preview-drawer { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.4); display: flex; justify-content: flex-end; z-index: 50; }
.preview-drawer__panel { width: min(480px, 92vw); height: 100%; background: var(--panel-bg, #fff); box-shadow: -2px 0 12px rgba(0, 0, 0, 0.2); display: flex; flex-direction: column; }
.preview-drawer__header { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border, #ddd); }
.preview-drawer__title { margin: 0; font-size: 1rem; }
.preview-drawer__close { border: none; background: transparent; font-size: 1.4rem; line-height: 1; cursor: pointer; color: var(--muted, #888); padding: 0 0.25rem; }
.preview-drawer__body { padding: 1rem; overflow-y: auto; flex: 1; }
.preview-drawer__hint { color: var(--muted, #888); font-style: italic; }
.preview-drawer__error { color: var(--error, #c33); background: var(--error-bg, #fee); padding: 0.5rem 0.75rem; border-radius: 4px; }
.preview-drawer__subtitle { margin: 0 0 0.25rem; font-size: 0.85rem; color: var(--muted, #888); }
.preview-drawer__text { margin: 0 0 1rem; white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6; }
</style>