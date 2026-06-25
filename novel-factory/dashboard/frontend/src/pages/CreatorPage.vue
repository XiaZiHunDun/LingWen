<!--
  CreatorPage.vue — 创作者三栏：写 / 脉络 / 设定 + 卷纲锁定与偏离 diff
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

    <CreatorModeGuidePanel :mode-label="modeLabel" />

    <CreatorVolumePlanShareModals />

    <CreatorOnboardingWizardPanel />
  </div>
</template>

<script setup>
import CreatorPageHeader from '../components/creator/CreatorPageHeader.vue';
import CreatorPageBanners from '../components/creator/CreatorPageBanners.vue';
import CreatorWorkspaceShell from '../components/creator/CreatorWorkspaceShell.vue';
import CreatorPulsePanel from '../components/creator/CreatorPulsePanel.vue';
import CreatorVolumePlanShareModals from '../components/creator/CreatorVolumePlanShareModals.vue';
import CreatorModeGuidePanel from '../components/creator/CreatorModeGuidePanel.vue';
import CreatorOnboardingWizardPanel from '../components/creator/CreatorOnboardingWizardPanel.vue';
import CreatorSettingsPanel from '../components/creator/CreatorSettingsPanel.vue';
import CreatorWritePanel from '../components/creator/CreatorWritePanel.vue';
import { useCreatorPage } from '../composables/useCreatorPage.js';

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
