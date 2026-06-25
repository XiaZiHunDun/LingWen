<!--
  CreatorPageLayout.vue — 创作页完整布局
-->
<template>
  <div class="creator-page">
    <CreatorPageHeader />
    <CreatorPageBanners />
    <CreatorWorkspaceShell>
      <CreatorWritePanel />
      <CreatorPulsePanel />
      <CreatorSettingsPanel />
    </CreatorWorkspaceShell>
    <CreatorModeGuidePanel />
    <CreatorVolumePlanShareModals />
    <CreatorOnboardingWizardPanel />
  </div>
</template>

<script setup>
import CreatorPageHeader from './CreatorPageHeader.vue';
import CreatorPageBanners from './CreatorPageBanners.vue';
import CreatorWorkspaceShell from './CreatorWorkspaceShell.vue';
import CreatorPulsePanel from './CreatorPulsePanel.vue';
import CreatorVolumePlanShareModals from './CreatorVolumePlanShareModals.vue';
import CreatorModeGuidePanel from './CreatorModeGuidePanel.vue';
import CreatorOnboardingWizardPanel from './CreatorOnboardingWizardPanel.vue';
import CreatorSettingsPanel from './CreatorSettingsPanel.vue';
import CreatorWritePanel from './CreatorWritePanel.vue';
import { useCreatorPage } from '../../composables/useCreatorPage.js';

useCreatorPage();
</script>

<style scoped>
.creator-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
</style>
