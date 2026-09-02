<!--
  PilotPage.vue — Phase 23 Task 12 (Part E1)
  Pilot 流水线总入口：组装 PilotStartForm + PilotLivePanel + PilotHistoryList + PilotCancelDialog。
  usePilotBatch 拿状态，useStudioProject 拿当前 slug。
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useStudioProject } from '@/composables';
import { usePilotBatch } from '@/composables/usePilotBatch';
import type { BatchEventType } from '@/composables/useBatchEventStream';
import PilotStartForm from '@/components/pilot/PilotStartForm.vue';
import PilotLivePanel from '@/components/pilot/PilotLivePanel.vue';
import PilotHistoryList from '@/components/pilot/PilotHistoryList.vue';
import PilotCancelDialog from '@/components/pilot/PilotCancelDialog.vue';

const studio = useStudioProject();
const pilot = usePilotBatch();

const cancelDialogJobId = ref<string | null>(null);
const eta = ref<number | null>(null);

onMounted(async () => {
  await pilot.refreshActive();
  const slug = studio.activeSlug ?? '';
  if (slug) await pilot.refreshHistory(slug);
});

async function onPreflight(payload: { slug: string; start_chapter: number; end_chapter: number }) {
  await pilot.runPreflight(payload);
}

async function onStart(payload: { slug: string; start_chapter: number; end_chapter: number; budget_usd: number; mode: 'canon' | 'pilot' }) {
  await pilot.startBatch(payload);
}

function onRequestCancel(jobId: string) {
  cancelDialogJobId.value = jobId;
}

async function onConfirmCancel() {
  if (!cancelDialogJobId.value) return;
  await pilot.cancelBatch(cancelDialogJobId.value);
  cancelDialogJobId.value = null;
}

function onHoldOn() {
  cancelDialogJobId.value = null;
}

function onToggleEventType(value: BatchEventType) {
  pilot.toggleEventType(value);
}
</script>

<template>
  <div class="pilot-page l1-page" data-testid="pilot-page">
    <div class="l1-page__body l1-panel-enter hub-l1__panel">
      <h1 class="page-title">Pilot 流水线</h1>
      <p v-if="pilot.startError.value" class="page-error pilot-page-error" data-testid="pilot-page-error" role="alert">{{ pilot.startError.value }}</p>
      <PilotStartForm
        :slug="studio.activeSlug ?? ''"
        :preflight-rows="pilot.preflightRows.value"
        :preflight-loading="pilot.preflightLoading.value"
        :start-loading="pilot.startLoading.value"
        :error="pilot.startError.value"
        @submit-preflight="onPreflight"
        @submit-start="onStart"
      />
      <PilotLivePanel
        :active-job="pilot.activeJob.value"
        :eta-seconds="eta"
        :cancel-loading="pilot.cancelLoading.value"
        :chapter-events="pilot.chapterEvents.value"
        :event-type-options="pilot.eventTypeOptions"
        :selected-event-types="pilot.selectedEventTypes.value"
        @request-cancel="onRequestCancel"
        @toggle-event-type="onToggleEventType"
      />
      <PilotHistoryList :history="pilot.history.value" />
      <PilotCancelDialog
        :visible="cancelDialogJobId !== null"
        :job-id="cancelDialogJobId ?? ''"
        :loading="pilot.cancelLoading.value"
        @confirm="onConfirmCancel"
        @hold-on="onHoldOn"
      />
    </div>
  </div>
</template>

<style scoped>
.pilot-page { padding: 1rem; }
.page-title { margin: 0 0 1rem; }
.page-error { color: var(--error, #c33); background: var(--error-bg, #fee); padding: 0.5rem 1rem; border-radius: 4px; margin-bottom: 1rem; }
</style>