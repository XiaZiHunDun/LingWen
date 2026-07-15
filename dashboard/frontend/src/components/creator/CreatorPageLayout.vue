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
        <CreatorSettingsPanel />
      </CreatorWorkspaceShell>
    </div>
    <CreatorModeGuidePanel />
    <CreatorVolumePlanShareModals />
    <CreatorOnboardingWizardPanel />
    <CreatorExportModal />
    <CreatorPublishWizardModal />
    <CreatorPublishHistoryModal />
  </div>
</template>

<script setup>
import CreatorPageHeader from './CreatorPageHeader.vue';
import CreatorPageBanners from './CreatorPageBanners.vue';
import CreatorInterventionBanner from './CreatorInterventionBanner.vue';
import CreatorWorkspaceShell from './CreatorWorkspaceShell.vue';
import CreatorPulsePanel from './CreatorPulsePanel.vue';
import CreatorVolumePlanShareModals from './CreatorVolumePlanShareModals.vue';
import CreatorModeGuidePanel from './CreatorModeGuidePanel.vue';
import CreatorOnboardingWizardPanel from './CreatorOnboardingWizardPanel.vue';
import CreatorSettingsPanel from './CreatorSettingsPanel.vue';
import CreatorWritePanel from './CreatorWritePanel.vue';
import CreatorMemoryPanel from './CreatorMemoryPanel.vue';
import CreatorExportModal from './CreatorExportModal.vue';
import CreatorPublishWizardModal from './CreatorPublishWizardModal.vue';
import CreatorPublishHistoryModal from './CreatorPublishHistoryModal.vue';
import { useCreatorPage } from '../../composables/useCreatorPage.js';

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
