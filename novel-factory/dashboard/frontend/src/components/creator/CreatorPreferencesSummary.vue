<!--
  CreatorPreferencesSummary.vue — 当前生效偏好摘要（模型 / RAG）
-->
<template>
  <p
    class="prefs-summary pixel-border"
    :class="{ 'prefs-summary--compact': compact }"
    data-testid="creator-preferences-summary"
    :title="pt.preferencesSummary"
  >
    <span class="prefs-summary__label">当前偏好</span>
    <span class="prefs-summary__text">{{ pt.preferencesSummary }}</span>
    <button
      v-if="showEditLink"
      type="button"
      class="link-btn prefs-summary__link"
      data-testid="prefs-summary-goto-settings"
      @click="pt.setWorkspaceTab('settings')"
    >
      调整
    </button>
  </p>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

defineProps({
  compact: { type: Boolean, default: false },
  showEditLink: { type: Boolean, default: true },
});

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);
</script>

<style scoped>
.prefs-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  margin: 0 0 var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-xs);
  background: var(--color-advance-bg-subtle);
}

.prefs-summary--compact {
  margin: 0;
  padding: 2px 8px;
  border: none;
  background: var(--color-advance-bg-soft);
}

.prefs-summary__label {
  font-weight: 600;
  color: var(--color-advance);
}

.prefs-summary__text {
  color: var(--text-muted, #555);
}

.prefs-summary__link {
  margin-left: auto;
  font-size: var(--text-xs);
}
</style>
