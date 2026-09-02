import { computed, onBeforeUnmount, ref } from 'vue';

import type {
  StudioBatchJobResponseDTO,
  StudioBatchJobSummaryDTO,
} from '@lingwen/dashboard-contracts/shared';

import {
  cancelStudioBatchJob,
  fetchStudioActiveBatchJob,
  listStudioBatchJobs,
  studioProductionRun,
} from '@/api/studio';

const POLL_INTERVAL_MS = 3000;

export interface PilotForm {
  slug: string;
  start_chapter: number;
  end_chapter: number;
  budget_usd: number;
  mode: 'canon' | 'pilot';
}

export function usePilotBatch() {
  const activeJob = ref<StudioBatchJobResponseDTO | null>(null);
  const history = ref<StudioBatchJobSummaryDTO[]>([]);
  const preflightRows = ref<Array<{ chapter: number; ok: boolean; message: string }>>([]);
  const preflightLoading = ref(false);
  const preflightError = ref<string | null>(null);
  const startLoading = ref(false);
  const startError = ref<string | null>(null);
  const cancelLoading = ref(false);
  const cancelError = ref<string | null>(null);

  let pollHandle: ReturnType<typeof setInterval> | null = null;

  function stopPolling() {
    if (pollHandle !== null) {
      clearInterval(pollHandle);
      pollHandle = null;
    }
  }

  function startPolling() {
    stopPolling();
    pollHandle = setInterval(() => {
      void refreshActive();
    }, POLL_INTERVAL_MS);
  }

  async function refreshActive(): Promise<void> {
    try {
      activeJob.value = await fetchStudioActiveBatchJob();
      if (activeJob.value?.status === 'running') {
        startPolling();
      } else {
        stopPolling();
      }
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
      // For now, surface form validation only
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
      startPolling();
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

  onBeforeUnmount(() => stopPolling());

  return {
    activeJob,
    history,
    preflightRows,
    preflightLoading,
    preflightError,
    startLoading,
    startError,
    cancelLoading,
    cancelError,
    isJobActive,
    refreshActive,
    refreshHistory,
    runPreflight,
    startBatch,
    cancelBatch,
  };
}