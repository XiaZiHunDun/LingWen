<!--
  CreatorPageLayout.vue — 创作页完整布局（从 CreatorPage 拆出）
-->
<template>
  <div class="creator-page">
    <CreatorPageHeader
      :overview="overview"
      :loading="loading"
      :ui-profile="uiProfile"
      :mode-label="modeLabel"
      :creation-mode-badge-hint-text="creationModeBadgeHintText"
      :mode-badge-hint-enabled="modeBadgeHintEnabled"
      :display-deviation-badge="displayDeviationBadge"
      :display-deviation-count="displayDeviationCount"
      :workspace-tabs-enabled="workspaceTabsEnabled"
      @refresh="refresh"
      @deviation-badge-click="onDeviationBadgeClick"
      @mode-badge-hint="showCreationModeBadgeHint"
    />

    <CreatorPageBanners
      :error="error"
      :conflict-message="conflictMessage"
      :save-message="saveMessage"
      @reload="refresh"
    />

    <CreatorWorkspaceShell
      v-model:active-tab="workspaceActiveTab"
      :overview="overview"
      :tabs-enabled="workspaceTabsEnabled"
      :workspace-tabs="workspaceTabs"
      :tab-badges="workspaceTabBadges"
    >
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

const {
  overview,
  loading,
  uiProfile,
  modeLabel,
  creationModeBadgeHintText,
  modeBadgeHintEnabled,
  displayDeviationBadge,
  displayDeviationCount,
  showCreationModeBadgeHint,
  workspaceActiveTab,
  workspaceTabsEnabled,
  workspaceTabs,
  workspaceTabBadges,
  onDeviationBadgeClick,
  error,
  conflictMessage,
  saveMessage,
  refresh,
} = useCreatorPage();
</script>

<style scoped>
.creator-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
</style>
