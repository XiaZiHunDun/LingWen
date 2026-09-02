<!--
  PilotLivePanel.vue — 实时状态：状态徽标 + 章节范围 + ETA + log tail + Cancel（P1）
-->
<template>
  <section class="pilot-live-panel pixel-card" data-testid="pilot-live-panel">
    <h2 class="section-title">实时状态</h2>
    <p v-if="!activeJob" class="empty-msg" data-testid="pilot-live-empty">无正在运行的 batch</p>
    <div v-else class="live-content">
      <div class="status-row">
        <span class="status-label">状态:</span>
        <strong :class="`job-status-${statusColor}`" data-testid="pilot-status">{{ activeJob.status }}</strong>
        <span class="chapter-range">{{ chapterRange }}</span>
        <span class="budget">${{ activeJob.budget_usd }}</span>
        <span v-if="activeJob.pid" class="pid">pid: {{ activeJob.pid }}</span>
      </div>
      <div class="eta-row">
        <span class="eta-label">预计剩余:</span>
        <span class="eta-value" data-testid="pilot-eta">{{ etaDisplay }}</span>
      </div>
      <pre v-if="activeJob.log_tail" class="log-tail" data-testid="pilot-log-tail">{{ activeJob.log_tail }}</pre>
      <div class="actions-row">
        <button v-if="activeJob.status === 'running'" type="button" class="cancel-btn pixel-border" data-testid="pilot-cancel-btn" :disabled="cancelLoading" @click="emit('request-cancel', activeJob.job_id)">
          {{ cancelLoading ? '取消中…' : 'Cancel' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface ActiveJob {
  job_id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  start_chapter: number;
  end_chapter: number;
  budget_usd: number;
  pid?: number | null;
  log_path?: string;
  log_tail?: string | null;
  started_at: string;
  finished_at?: string | null;
  exit_code?: number | null;
  error?: string | null;
}

const props = defineProps<{
  activeJob: ActiveJob | null;
  etaSeconds: number | null;
  cancelLoading: boolean;
}>();

const emit = defineEmits<{ 'request-cancel': [jobId: string] }>();

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
.log-tail { background: var(--code-bg, #1e1e1e); color: var(--code-f, #ddd); padding: 0.5rem; border-radius: 4px; max-height: 200px; overflow-y: auto; font-size: 0.85rem; }
.empty-msg { color: var(--muted, #888); font-style: italic; }
.cancel-btn { padding: 0.4rem 0.8rem; cursor: pointer; background: var(--error-bg, #fee); color: var(--error, #c33); border-color: var(--error, #c33); }
</style>