<!--
  CreatorPageHeader.vue — 创作页顶栏（inject 页级 chrome 上下文）
-->
<template>
  <header class="page-header">
    <h1 class="page-title" data-testid="page-title">创作伴侣</h1>
    <div class="header-actions">
      <span
        v-if="c.overview"
        class="mode-badge pixel-border"
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
        v-if="c.overview && c.displayDeviationBadge"
        class="deviation-badge pixel-border deviation-badge--clickable"
        data-testid="deviation-badge"
        role="button"
        tabindex="0"
        :title="c.workspaceTabsEnabled ? '查看脉络与偏离' : undefined"
        @click="c.onDeviationBadgeClick"
        @keydown.enter="c.onDeviationBadgeClick"
      >
        偏离 {{ c.displayDeviationCount }}
      </span>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="c.loading"
        @click="c.refresh"
      >
        {{ c.loading ? '加载中…' : '刷新' }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';

const c = inject(CREATOR_PAGE_CHROME_KEY);
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.page-title {
  font-size: 14px;
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.mode-badge,
.deviation-badge {
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  font-family: 'Press Start 2P', monospace;
}

.deviation-badge {
  color: #c44;
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
  color: #2a6;
  background: rgba(80, 180, 120, 0.15);
  box-shadow: inset 0 0 0 1px rgba(60, 140, 90, 0.45);
}

.mode-badge--advance-tint {
  color: #36a;
  background: rgba(80, 140, 220, 0.15);
  box-shadow: inset 0 0 0 1px rgba(60, 110, 180, 0.45);
}

.mode-badge--studio-tint {
  color: #a63;
  background: rgba(200, 140, 80, 0.15);
  box-shadow: inset 0 0 0 1px rgba(160, 110, 60, 0.45);
}

.refresh-btn {
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  cursor: pointer;
}
</style>
