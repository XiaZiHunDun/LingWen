<template>
  <header class="page-header creator-page-header" v-if="c.overview">
    <div class="creator-page-header__row">
      <div class="creator-page-header__left">
        <div class="creator-page-header__badges">
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
            ⚠️ 偏离 {{ c.displayDeviationCount }}
          </span>
        </div>
      </div>
      <div class="creator-page-header__actions">
        <button
          v-if="c.showHeaderRefresh"
          class="refresh-btn pixel-border"
          data-testid="refresh-btn"
          :disabled="c.loading"
          @click="c.refresh"
        >
          {{ c.loading ? '加载中…' : '🔄 刷新' }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';

const c = inject(CREATOR_PAGE_CHROME_KEY);
</script>

<style scoped>
.creator-page-header__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.creator-page-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.creator-page-header__badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
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
