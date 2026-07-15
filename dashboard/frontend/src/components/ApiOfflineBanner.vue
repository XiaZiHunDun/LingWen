<!--
  ApiOfflineBanner.vue — 全局 API 离线提示（替代各页重复红条）
-->
<template>
  <div
    v-if="offline"
    class="api-offline-banner pixel-border"
    data-testid="api-offline-banner"
    role="alert"
    aria-live="assertive"
  >
    <span class="api-offline-banner__text">{{ message }}</span>
    <button
      type="button"
      class="api-offline-banner__retry pixel-border"
      data-testid="api-offline-retry-btn"
      :disabled="checking"
      @click="$emit('retry')"
    >
      {{ checking ? '检测中…' : '重试连接' }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  offline: { type: Boolean, default: false },
  message: { type: String, default: '' },
  checking: { type: Boolean, default: false },
});

defineEmits(['retry']);
</script>

<style scoped>
.api-offline-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin: 0 var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: #fde8e8;
  color: #8b1a1a;
  font-size: var(--text-sm);
  font-family: var(--font-ui);
}

.api-offline-banner__text {
  flex: 1;
  min-width: 12rem;
}

.api-offline-banner__retry {
  font-size: var(--text-xs);
  padding: 4px 10px;
  background: var(--bg-secondary);
  cursor: pointer;
}

.api-offline-banner__retry:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
