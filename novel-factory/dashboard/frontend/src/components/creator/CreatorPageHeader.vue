<!--
  CreatorPageHeader.vue — 创作页顶栏（从 CreatorPage 拆出）
-->
<template>
  <header class="page-header">
    <h1 class="page-title" data-testid="page-title">创作伴侣</h1>
    <div class="header-actions">
      <span
        v-if="overview"
        class="mode-badge pixel-border"
        :class="{
          'mode-badge--hintable': modeBadgeHintEnabled && creationModeBadgeHintText,
          'mode-badge--companion-tint': uiProfile.companion_creation_mode_badge_tint && overview.creation_mode === 'companion',
          'mode-badge--advance-tint': uiProfile.advance_creation_mode_badge_tint && overview.creation_mode === 'advance',
          'mode-badge--studio-tint': uiProfile.studio_creation_mode_badge_tint && overview.creation_mode === 'studio',
        }"
        data-testid="creation-mode-badge"
        :title="modeBadgeHintEnabled ? creationModeBadgeHintText : undefined"
        @click="$emit('mode-badge-hint')"
      >
        {{ modeLabel }}
      </span>
      <span
        v-if="overview && displayDeviationBadge"
        class="deviation-badge pixel-border deviation-badge--clickable"
        data-testid="deviation-badge"
        role="button"
        tabindex="0"
        :title="workspaceTabsEnabled ? '查看脉络与偏离' : undefined"
        @click="$emit('deviation-badge-click')"
        @keydown.enter="$emit('deviation-badge-click')"
      >
        偏离 {{ displayDeviationCount }}
      </span>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="loading"
        @click="$emit('refresh')"
      >
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  overview: { type: Object, default: null },
  loading: { type: Boolean, required: true },
  uiProfile: { type: Object, required: true },
  modeLabel: { type: String, default: '' },
  creationModeBadgeHintText: { type: String, default: '' },
  modeBadgeHintEnabled: { type: Boolean, default: false },
  displayDeviationBadge: { type: Boolean, default: false },
  displayDeviationCount: { type: Number, default: 0 },
  workspaceTabsEnabled: { type: Boolean, default: false },
});

defineEmits(['refresh', 'deviation-badge-click', 'mode-badge-hint']);
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
