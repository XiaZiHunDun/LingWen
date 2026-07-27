<!--
  CreatorPageLayout.vue — 创作页完整布局
-->
<template>
  <div class="creator-page l1-page" data-testid="creator-page">
    <CreatorPageHeader />
    <CreatorPageBanners />
    <CreatorInterventionBanner />
    <div class="creator-page__body">
      <CreatorWorkspaceShell>
        <CreatorWritePanel />
        <CreatorPulsePanel />
        <CreatorMemoryPanel />
      </CreatorWorkspaceShell>
    </div>
    <CreatorVolumePlanShareModals />
    <CreatorExportModal />
    <CreatorPublishWizardModal />
    <CreatorPublishHistoryModal />
  </div>
</template>

<script setup>
import { defineAsyncComponent } from 'vue';
import CreatorPageHeader from './CreatorPageHeader.vue';
import CreatorPageBanners from './CreatorPageBanners.vue';
import CreatorInterventionBanner from './CreatorInterventionBanner.vue';
import CreatorWorkspaceShell from './CreatorWorkspaceShell.vue';
import CreatorPulsePanel from './CreatorPulsePanel.vue';
import CreatorWritePanel from './CreatorWritePanel.vue';
import CreatorMemoryPanel from './CreatorMemoryPanel.vue';
import { useCreatorPage } from '../../composables/index.js';

const CreatorVolumePlanShareModals = defineAsyncComponent(() => import('./CreatorVolumePlanShareModals.vue'));
const CreatorExportModal = defineAsyncComponent(() => import('./CreatorExportModal.vue'));
const CreatorPublishWizardModal = defineAsyncComponent(() => import('./CreatorPublishWizardModal.vue'));
const CreatorPublishHistoryModal = defineAsyncComponent(() => import('./CreatorPublishHistoryModal.vue'));

useCreatorPage();
</script>

<style scoped>
.creator-page {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.creator-page__body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
