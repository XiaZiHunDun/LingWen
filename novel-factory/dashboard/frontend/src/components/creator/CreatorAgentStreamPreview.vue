<!--
  CreatorAgentStreamPreview.vue — Agent 生成流式预览（SSE chunk / advice）
-->
<template>
  <div class="agent-stream-preview pixel-border" data-testid="agent-stream-preview">
    <div class="agent-stream-preview__head">
      <span class="agent-stream-preview__title">
        {{ adviceLines.length ? '导演建议生成中' : '候选预览生成中' }}
      </span>
      <span v-if="previewLabel && !adviceLines.length" class="meta-line">{{ previewLabel }}</span>
    </div>
    <ul v-if="adviceLines.length" class="agent-stream-preview__advice">
      <li v-for="(line, idx) in adviceLines" :key="idx">{{ line }}</li>
    </ul>
    <pre v-else class="agent-stream-preview__text">{{ previewText }}<span class="agent-stream-preview__cursor">▍</span></pre>
  </div>
</template>

<script setup>
defineProps({
  previewText: { type: String, default: '' },
  previewLabel: { type: String, default: '' },
  adviceLines: { type: Array, default: () => [] },
});
</script>

<style scoped>
.agent-stream-preview {
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border-radius: 8px;
}

.agent-stream-preview__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.agent-stream-preview__title {
  font-size: var(--text-xs);
  font-weight: 600;
}

.agent-stream-preview__text {
  margin: 0;
  white-space: pre-wrap;
  font-size: var(--text-xs);
  line-height: 1.5;
  max-height: 180px;
  overflow: auto;
}

.agent-stream-preview__cursor {
  animation: agent-stream-blink 1s step-end infinite;
}

.agent-stream-preview__advice {
  margin: 0;
  padding-left: 1.1rem;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

@keyframes agent-stream-blink {
  50% {
    opacity: 0;
  }
}
</style>
