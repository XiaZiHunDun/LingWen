<!--
  PageLeadBar.vue — 可收起的页面说明（P0）
-->
<template>
  <header
    v-if="visible"
    class="page-lead-bar"
    :class="{ 'page-lead-bar--inline': inline }"
    :data-testid="`page-lead-bar-${pageId}`"
  >
    <p class="page-lead">{{ text }}</p>
    <button
      type="button"
      class="page-lead-bar__dismiss"
      :data-testid="`page-lead-dismiss-${pageId}`"
      @click="dismiss"
    >
      知道了
    </button>
  </header>
</template>

<script setup>
import { usePageLeadDismiss } from '../composables/usePageLeadDismiss.js';

const props = defineProps({
  pageId: { type: String, required: true },
  text: { type: String, required: true },
  /** 嵌入卡片内的轻量提示样式 */
  inline: { type: Boolean, default: false },
});

const { visible, dismiss } = usePageLeadDismiss(props.pageId);
</script>

<style scoped>
.page-lead-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-xs);
}
.page-lead-bar .page-lead {
  flex: 1;
}
.page-lead-bar__dismiss {
  flex-shrink: 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  background: none;
  border: none;
  padding: 2px 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.page-lead-bar__dismiss:hover {
  color: var(--color-accent);
}

.page-lead-bar--inline {
  align-items: center;
  margin-bottom: 0;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-muted);
  border-radius: var(--radius-md);
}
.page-lead-bar--inline .page-lead {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  line-height: var(--leading-normal);
}
.page-lead-bar--inline .page-lead-bar__dismiss {
  font-size: 11px;
}
</style>
