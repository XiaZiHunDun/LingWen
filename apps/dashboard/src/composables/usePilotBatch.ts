import { computed, onBeforeUnmount, ref, watch } from 'vue';

import {
  cancelStudioBatchJob,
  fetchStudioActiveBatchJob,
  listStudioBatchJobs,
  studioProductionRun,
} from '@/api/studio';
import type {
  StudioBatchJobResponseDTO,
  StudioBatchJobSummaryDTO,
} from '@/api/studio';
import { useBatchEventStream } from '@/composables/useBatchEventStream';
import type { BatchEvent, BatchEventType } from '@/composables/useBatchEventStream';

/** Fallback REST polling interval used only while the SSE stream is disconnected. */
const FALLBACK_POLL_INTERVAL_MS = 5000;
/** Keep the most recent chapter_completed entries for the LivePanel list. */
const CHAPTER_EVENTS_CAP = 20;
const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled']);

/** Lightweight live-filter options shown as toggle chips in the live panel. */
const EVENT_TYPE_OPTIONS: ReadonlyArray<{ value: BatchEventType; label: string }> = [
  { value: 'job_state', label: '状态' },
  { value: 'chapter_started', label: '章节开始' },
  { value: 'chapter_completed', label: '章节完成' },
  { value: 'job_completed', label: '完成' },
  { value: 'job_failed', label: '失败' },
  { value: 'job_cancelled', label: '取消' },
];

export interface PilotForm {
  slug: string;
  start_chapter: number;
  end_chapter: number;
  budget_usd: number;
  mode: 'canon' | 'pilot';
}

export interface ChapterProgressEvent {
  chapter_num: number;
  receivedAt: string;
}

export function usePilotBatch() {
  const activeJob = ref<StudioBatchJobResponseDTO | null>(null);
  const history = ref<StudioBatchJobSummaryDTO[]>([]);
  const chapterEvents = ref<ChapterProgressEvent[]>([]);
  const preflightRows = ref<Array<{ chapter: number; ok: boolean; message: string }>>([]);
  const preflightLoading = ref(false);
  const preflightError = ref<string | null>(null);
  const startLoading = ref(false);
  const startError = ref<string | null>(null);
  const cancelLoading = ref(false);
  const cancelError = ref<string | null>(null);

  const activeJobId = computed(() => activeJob.value?.job_id ?? null);
  // Empty selection = no `event_types` filter → server streams all event types
  // (Phase 25 carryover: live filter UI wires these into the SSE query).
  const selectedEventTypes = ref<BatchEventType[]>([]);
  // replay=true: on any connect the server replays deterministic chapter history
  // from disk, so chapterEvents is never left empty after a reload/reconnect.
  const { events, isConnected, lastError } = useBatchEventStream(activeJobId, {
    replay: true,
    eventTypes: selectedEventTypes,
  });

  function toggleEventType(type: BatchEventType): void {
    selectedEventTypes.value = selectedEventTypes.value.includes(type)
      ? selectedEventTypes.value.filter((t) => t !== type)
      : [...selectedEventTypes.value, type];
  }

  let fallbackPoll: ReturnType<typeof setInterval> | null = null;
  let processedEventIndex = 0;

  function isTerminal(status: string | null | undefined): boolean {
    return status ? TERMINAL_STATUSES.has(status) : false;
  }

  function stopFallbackPolling() {
    if (fallbackPoll !== null) {
      clearInterval(fallbackPoll);
      fallbackPoll = null;
    }
  }

  function startFallbackPolling() {
    stopFallbackPolling();
    if (isTerminal(activeJob.value?.status) || !activeJobId.value) return;
    fallbackPoll = setInterval(() => {
      void refreshActive();
    }, FALLBACK_POLL_INTERVAL_MS);
  }

  function syncFallbackPolling() {
    if (isConnected.value || isTerminal(activeJob.value?.status) || !activeJobId.value) {
      stopFallbackPolling();
    } else if (activeJobId.value) {
      startFallbackPolling();
    }
  }

  function applyEvent(event: BatchEvent): void {
    const data = event.data;
    switch (event.type) {
      case 'job_state': {
        if (typeof data.job_id === 'string') {
          activeJob.value = data as unknown as StudioBatchJobResponseDTO;
        }
        break;
      }
      case 'chapter_completed': {
        if (typeof data.chapter_num === 'number') {
          chapterEvents.value = [
            ...chapterEvents.value,
            { chapter_num: data.chapter_num, receivedAt: event.receivedAt },
          ].slice(-CHAPTER_EVENTS_CAP);
        }
        break;
      }
      case 'job_completed':
      case 'job_failed':
      case 'job_cancelled': {
        if (!activeJob.value) break;
        const newStatus: StudioBatchJobResponseDTO['status'] =
          event.type === 'job_completed'
            ? 'completed'
            : event.type === 'job_failed'
              ? 'failed'
              : 'cancelled';
        activeJob.value = {
          ...activeJob.value,
          status: newStatus,
          finished_at:
            typeof data.finished_at === 'string' ? data.finished_at : activeJob.value.finished_at,
          exit_code:
            typeof data.exit_code === 'number' ? data.exit_code : activeJob.value.exit_code,
        };
        break;
      }
      default:
        break;
    }
  }

  // Reset stream-scoped state whenever the active job changes.
  watch(activeJobId, () => {
    processedEventIndex = 0;
    chapterEvents.value = [];
    stopFallbackPolling();
  });

  // Consume SSE events (each exactly once) and keep fallback polling in sync.
  watch([events, () => activeJob.value?.status, isConnected], () => {
    const list = events.value;
    for (let i = processedEventIndex; i < list.length; i += 1) {
      applyEvent(list[i]);
    }
    processedEventIndex = list.length;
    syncFallbackPolling();
  });

  async function refreshActive(): Promise<void> {
    try {
      activeJob.value = await fetchStudioActiveBatchJob();
      syncFallbackPolling();
    } catch (err) {
      console.warn('[usePilotBatch] refreshActive failed', err);
    }
  }

  async function refreshHistory(slug: string, limit = 20): Promise<void> {
    try {
      const result = await listStudioBatchJobs(slug, limit);
      history.value = result.jobs;
    } catch (err) {
      console.warn('[usePilotBatch] refreshHistory failed', err);
    }
  }

  async function runPreflight(_form: PilotForm): Promise<void> {
    preflightLoading.value = true;
    preflightError.value = null;
    try {
      // TODO Phase 24+: dedicated preflight wrapper; reuse studio preflight helper
      preflightRows.value = [];
    } finally {
      preflightLoading.value = false;
    }
  }

  async function startBatch(form: PilotForm): Promise<void> {
    startLoading.value = true;
    startError.value = null;
    try {
      const { slug: _slug, ...rest } = form;
      const job = await studioProductionRun(rest);
      activeJob.value = job;
      syncFallbackPolling();
    } catch (err) {
      startError.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      startLoading.value = false;
    }
  }

  async function cancelBatch(jobId: string): Promise<void> {
    cancelLoading.value = true;
    cancelError.value = null;
    try {
      await cancelStudioBatchJob(jobId);
      await refreshActive();
    } catch (err) {
      cancelError.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      cancelLoading.value = false;
    }
  }

  const isJobActive = computed(() => activeJob.value?.status === 'running');

  onBeforeUnmount(() => stopFallbackPolling());

  return {
    activeJob,
    history,
    chapterEvents,
    preflightRows,
    preflightLoading,
    preflightError,
    startLoading,
    startError,
    cancelLoading,
    cancelError,
    isConnected,
    lastError,
    isJobActive,
    eventTypeOptions: EVENT_TYPE_OPTIONS,
    selectedEventTypes,
    toggleEventType,
    refreshActive,
    refreshHistory,
    runPreflight,
    startBatch,
    cancelBatch,
  };
}