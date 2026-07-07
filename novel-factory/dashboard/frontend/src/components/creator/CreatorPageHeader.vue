<!--
  CreatorPageHeader.vue — 创作页顶栏（inject 页级 chrome 上下文）
-->
<template>
  <header class="page-header creator-page-header">
    <div v-if="c.showPageTitle || c.displayDeviationBadge" class="creator-page-header__row">
      <h1 v-if="c.showPageTitle" class="page-title" data-testid="page-title">书桌</h1>
      <div v-if="c.overview" class="creator-page-header__badges">
        <span
          v-if="c.showCreationModeBadge"
          class="mode-badge creator-badge pixel-border"
          :class="{
            'mode-badge--hintable': c.modeBadgeHintEnabled && c.creationModeBadgeHintText,
            'mode-badge--companion-tint': c.uiProfile.companion_creation_mode_badge_tint && c.overview.creation_mode === 'companion',
            'mode-badge--advance-tint': c.uiProfile.advance_creation_mode_badge_tint && c.overview.creation_mode === 'advance',
            'mode-badge--studio-tint': c.uiProfile.studio_creation_mode_badge_tint && c.overview.creation_mode === 'studio',
          }"
          data-testid="creation-mode-badge"
          :title="c.modeBadgeHintEnabled ? c.creationModeBadgeHintText : undefined"
          @click="c.showCreationModeBadgeHint"
        >
          {{ c.modeLabel }}
        </span>
        <span
          v-if="c.displayDeviationBadge"
          class="deviation-badge creator-badge pixel-border deviation-badge--clickable"
          data-testid="deviation-badge"
          role="button"
          tabindex="0"
          :title="c.workspaceTabsEnabled ? '查看脉络与偏离' : undefined"
          @click="c.onDeviationBadgeClick"
          @keydown.enter="c.onDeviationBadgeClick"
        >
          偏离 {{ c.displayDeviationCount }}
        </span>
      </div>
    </div>

    <div
      v-if="c.overview && c.showHeaderActionsRow"
      class="creator-page-header__row creator-page-header__row--prefs"
      :class="{ 'creator-page-header__row--actions-only': !c.showHeaderPreferences && !c.showHeaderPublishExport }"
    >
      <CreatorPreferencesSummary
        v-if="c.overview && c.showHeaderPreferences"
        compact
        :show-edit-link="true"
        class="header-prefs-summary"
      />
      <div class="creator-page-header__actions">
        <button
          v-if="c.showHeaderPublishExport"
          class="action-btn pixel-border"
          data-testid="export-btn"
          :disabled="!c.overview"
          @click="c.openExportModal('full')"
        >
          导出
        </button>
        <button
          v-if="c.showHeaderPublishExport"
          class="action-btn pixel-border"
          data-testid="publish-btn"
          :disabled="!c.overview"
          @click="c.openPublishWizard"
        >
          发布
        </button>
        <button
          v-if="c.showHeaderRefresh"
          class="refresh-btn pixel-border"
          data-testid="refresh-btn"
          :disabled="c.loading"
          @click="c.refresh"
        >
          {{ c.loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';
import CreatorPreferencesSummary from './CreatorPreferencesSummary.vue';

const c = inject(CREATOR_PAGE_CHROME_KEY);
</script>

<style scoped>
.creator-page-header__row--actions-only {
  justify-content: flex-end;
}

.creator-page-header__row--prefs {
  align-items: center;
}

.creator-page-header__badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
}

.header-prefs-summary {
  flex: 1;
  min-width: min(320px, 100%);
  max-width: 100%;
}

.deviation-badge {
  color: var(--color-danger);
}

.deviation-badge--clickable {
  cursor: pointer;
}

.deviation-badge--clickable:hover {
  outline: 2px solid var(--color-accent);
}

.mode-badge--hintable {
  cursor: help;
}

.mode-badge--companion-tint {
  color: var(--color-accent);
  background: var(--color-accent-soft);
  box-shadow: inset 0 0 0 1px rgba(61, 95, 138, 0.35);
}

.mode-badge--advance-tint {
  color: var(--color-advance);
  background: var(--color-advance-soft);
  box-shadow: inset 0 0 0 1px var(--color-advance-border);
}

.mode-badge--studio-tint {
  color: #a63;
  background: rgba(200, 140, 80, 0.15);
  box-shadow: inset 0 0 0 1px rgba(160, 110, 60, 0.45);
}

.refresh-btn,
.action-btn {
  padding: 6px 12px;
  cursor: pointer;
}
</style>
