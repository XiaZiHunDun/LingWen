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
import PilotQueuePanel from '@/components/pilot/PilotQueuePanel.vue';
import PilotTemplatePanel from '@/components/pilot/PilotTemplatePanel.vue';
import PilotHistoryList from '@/components/pilot/PilotHistoryList.vue';
import PilotCancelDialog from '@/components/pilot/PilotCancelDialog.vue';

const studio = useStudioProject();
const pilot = usePilotBatch();
const startFormRef = ref<InstanceType<typeof PilotStartForm> | null>(null);

const cancelDialogJobId = ref<string | null>(null);
const eta = ref<number | null>(null);
const lastSlug = ref('');

onMounted(async () => {
  await pilot.refreshActive();
  const slug = studio.activeSlug ?? '';
  if (slug) {
    await pilot.refreshHistory(slug);
    await pilot.refreshQueue(slug);
    await pilot.loadTemplates(slug);
  }
});

async function onPreflight(payload: { slug: string; start_chapter: number; end_chapter: number }) {
  await pilot.runPreflight(payload);
}

async function onStart(payload: { slug: string; start_chapter: number; end_chapter: number; budget_usd: number; mode: 'canon' | 'pilot' }) {
  await pilot.startBatch(payload);
  lastSlug.value = payload.slug;
  if (payload.slug) await pilot.refreshQueue(payload.slug);
}

function onRequestCancel(jobId: string) {
  cancelDialogJobId.value = jobId;
}

async function onConfirmCancel() {
  if (!cancelDialogJobId.value) return;
  await pilot.cancelBatch(cancelDialogJobId.value);
  cancelDialogJobId.value = null;
  if (lastSlug.value) await pilot.refreshQueue(lastSlug.value);
}

function onHoldOn() {
  cancelDialogJobId.value = null;
}

function onToggleEventType(value: BatchEventType) {
  pilot.toggleEventType(value);
}

function onOpenPreview(chapterNum: number) {
  void pilot.openPreview(chapterNum);
}

function onClosePreview() {
  pilot.closePreview();
}

function onApplyTemplate(templateId: string) {
  const template = pilot.templates.value.find((t) => t.template_id === templateId);
  if (template && startFormRef.value) {
    startFormRef.value.fillFromTemplate(template);
  }
}

async function onSaveTemplate(payload: { name: string }) {
  const form = startFormRef.value?.currentForm;
  if (!form || !form.slug) return;
  await pilot.saveTemplate(payload.name, form);
}

async function onRemoveTemplate(templateId: string) {
  const slug = studio.activeSlug ?? '';
  if (slug) await pilot.deleteTemplate(templateId, slug);
}
</script>

<template>
  <div class="pilot-page l1-page" data-testid="pilot-page">
    <div class="l1-page__body l1-panel-enter hub-l1__panel">
      <h1 class="page-title">Pilot 流水线</h1>
      <p v-if="pilot.startError.value" class="page-error pilot-page-error" data-testid="pilot-page-error" role="alert">{{ pilot.startError.value }}</p>
      <PilotStartForm
        ref="startFormRef"
        :slug="studio.activeSlug ?? ''"
        :preflight-rows="pilot.preflightRows.value"
        :preflight-loading="pilot.preflightLoading.value"
        :start-loading="pilot.startLoading.value"
        :error="pilot.startError.value"
        @submit-preflight="onPreflight"
        @submit-start="onStart"
      />
      <PilotTemplatePanel
        :slug="studio.activeSlug ?? ''"
        :templates="pilot.templates.value"
        :loading="pilot.templateLoading.value"
        :save-loading="pilot.templateSaveLoading.value"
        :error="pilot.templateError.value"
        :message="pilot.templateMessage.value"
        @apply="onApplyTemplate"
        @remove="onRemoveTemplate"
        @save="onSaveTemplate"
      />
      <PilotLivePanel
        :active-job="pilot.activeJob.value"
        :eta-seconds="eta"
        :cancel-loading="pilot.cancelLoading.value"
        :chapter-events="pilot.chapterEvents.value"
        :event-type-options="pilot.eventTypeOptions"
        :selected-event-types="pilot.selectedEventTypes.value"
        :preview-chapter="pilot.previewChapter.value"
        :preview-data="pilot.previewData.value"
        :preview-loading="pilot.previewLoading.value"
        :preview-error="pilot.previewError.value"
        @request-cancel="onRequestCancel"
        @toggle-event-type="onToggleEventType"
        @open-preview="onOpenPreview"
        @close-preview="onClosePreview"
      />
      <PilotQueuePanel :queue="pilot.queue.value" />
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