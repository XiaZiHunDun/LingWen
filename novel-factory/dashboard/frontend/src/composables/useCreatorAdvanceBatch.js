/**
 * useCreatorAdvanceBatch — 推进 batch preflight / 运行 / 轮询（从 CreatorPage 抽出）
 */
import { computed, onUnmounted, ref } from 'vue';
import {
  generateCreatorVolumeSummary,
  studioProductionPreflight,
  studioProductionRun,
  fetchStudioActiveBatchJob,
} from '../api/index.js';
import { isPulseSubpanelVisible } from '../config/creatorPanelMatrix.js';

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   error: import('vue').Ref<string|null>,
 *   navigateTo: (page: string, opts?: object) => void,
 *   onAfterBatchRefresh: () => Promise<void>,
 *   onBatchCompleted: (start: number, end: number) => Promise<void>,
 *   loadBatchHistory: () => Promise<void>,
 *   setBatchSummaryPrompt: (prompt: object|null) => void,
 * }} deps
 */
export function useCreatorAdvanceBatch(deps) {
  const {
    uiProfile,
    overview,
    saveMessage,
    error,
    navigateTo,
    onAfterBatchRefresh,
    onBatchCompleted,
    loadBatchHistory,
    setBatchSummaryPrompt,
  } = deps;

  const batchStart = ref(1);
  const batchEnd = ref(10);
  const batchBudget = ref(0.3);
  const batchCommand = ref('');
  const preflightOk = ref(false);
  const batchRunning = ref(false);
  const batchError = ref(null);
  const batchJob = ref(null);
  const lastBatchStatus = ref(null);
  let batchPollTimer = null;

  const showAdvanceBatch = computed(
    () => isPulseSubpanelVisible(overview.value?.creation_mode, 'advanceBatch')
      || overview.value?.advance_volume_summary,
  );

  const showAdvanceBatchOnCreator = computed(
    () => uiProfile.value.advance_batch_panel_on_creator === true,
  );

  function goProduceConsole() {
    navigateTo('produce', { tab: 'studio', clearFocus: true });
  }

  async function runAdvancePreflight() {
    batchError.value = null;
    preflightOk.value = false;
    try {
      const data = await studioProductionPreflight({
        start_chapter: batchStart.value,
        end_chapter: batchEnd.value,
        budget_usd: batchBudget.value,
      });
      batchCommand.value = data.batch_command || '';
      preflightOk.value = Boolean(data.all_ok);
      if (!data.all_ok) {
        batchError.value = 'Preflight 未通过，请检查大纲与支柱';
      }
    } catch (e) {
      batchError.value = e instanceof Error ? e.message : String(e);
    }
  }

  function stopBatchPolling() {
    if (batchPollTimer) {
      clearInterval(batchPollTimer);
      batchPollTimer = null;
    }
  }

  async function pollBatchJob() {
    try {
      const job = await fetchStudioActiveBatchJob();
      if (job) {
        batchJob.value = job;
        batchRunning.value = job.status === 'running';
      } else if (batchJob.value?.status === 'running') {
        batchJob.value = { ...batchJob.value, status: 'completed' };
        batchRunning.value = false;
      }
    } catch {
      /* optional */
    }
  }

  function startBatchPolling() {
    stopBatchPolling();
    batchPollTimer = setInterval(async () => {
      const prev = lastBatchStatus.value;
      await pollBatchJob();
      const status = batchJob.value?.status ?? null;
      if (prev === 'running' && status === 'completed') {
        if (showAdvanceBatch.value && overview.value?.advance_volume_summary) {
          try {
            await generateCreatorVolumeSummary({
              startChapter: batchStart.value,
              endChapter: batchEnd.value,
            });
            setBatchSummaryPrompt({
              start: batchStart.value,
              end: batchEnd.value,
              alert_volume_labels: [],
            });
          } catch {
            /* volume summary optional */
          }
        }
        saveMessage.value = 'Batch 已完成，卷摘要已更新';
        await onAfterBatchRefresh();
        await onBatchCompleted(batchStart.value, batchEnd.value);
        await loadBatchHistory();
      }
      if (status === 'completed' || status === 'failed') {
        stopBatchPolling();
      }
      lastBatchStatus.value = status;
    }, 3000);
  }

  async function runAdvanceBatch() {
    batchError.value = null;
    batchRunning.value = true;
    try {
      batchJob.value = await studioProductionRun({
        start_chapter: batchStart.value,
        end_chapter: batchEnd.value,
        budget_usd: batchBudget.value,
      });
      lastBatchStatus.value = batchJob.value?.status ?? 'running';
      if (batchJob.value?.status === 'running') {
        startBatchPolling();
      }
    } catch (e) {
      batchError.value = e instanceof Error ? e.message : String(e);
    } finally {
      batchRunning.value = false;
    }
  }

  function resumeBatchPollingIfNeeded() {
    if (batchJob.value?.status === 'running' && !batchPollTimer) {
      lastBatchStatus.value = 'running';
      startBatchPolling();
    }
  }

  onUnmounted(() => {
    stopBatchPolling();
  });

  const panelContext = {
    showAdvanceBatch,
    showAdvanceBatchOnCreator,
    batchStart,
    batchEnd,
    batchBudget,
    batchRunning,
    preflightOk,
    batchCommand,
    batchError,
    batchJob,
    runAdvancePreflight,
    runAdvanceBatch,
    goProduceConsole,
  };

  return {
    panelContext,
    batchStart,
    batchEnd,
    batchBudget,
    batchRunning,
    batchJob,
    pollBatchJob,
    stopBatchPolling,
    resumeBatchPollingIfNeeded,
  };
}
