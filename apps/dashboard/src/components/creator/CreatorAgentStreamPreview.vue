<!--
  CreatorAgentStreamPreview.vue — Agent 生成流式预览（SSE chunk / advice）
-->
<template>
  <div
    class="agent-stream-preview pixel-border"
    :class="{ 'agent-stream-preview--llm': streamSource === 'llm' }"
    :data-testid="mainBar ? 'write-agent-stream-preview-main' : 'agent-stream-preview'"
  >
    <div class="agent-stream-preview__head">
      <span class="agent-stream-preview__title">{{ titleText }}</span>
      <span v-if="previewLabel && !adviceLines.length && streamSource !== 'llm'" class="meta-line">{{ previewLabel }}</span>
    </div>
    <ul v-if="adviceLines.length" class="agent-stream-preview__advice">
      <li v-for="(line, idx) in adviceLines" :key="idx">{{ line }}</li>
    </ul>
    <pre
      v-else
      class="agent-stream-preview__text"
      :class="{ 'agent-stream-preview__text--llm': streamSource === 'llm' && isLlmPlaceholder }"
    >{{ bodyText }}<span v-if="!isLlmPlaceholder" class="agent-stream-preview__cursor">▍</span></pre>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  previewText: { type: String, default: '' },
  displayText: { type: String, default: '' },
  previewLabel: { type: String, default: '' },
  adviceLines: { type: Array, default: () => [] },
  streamSource: { type: String, default: null },
  /** human-first 主区展示，与 advanced-tools 内预览区分 testid */
  mainBar: { type: Boolean, default: false },
});

const bodyText = computed(() => props.displayText || props.previewText);

const isLlmPlaceholder = computed(() =>
  props.streamSource === 'llm' && /^模型输出中/.test(bodyText.value || ''),
);

const titleText = computed(() => {
  if (props.adviceLines.length) return '导演建议生成中';
  if (props.streamSource === 'llm') return '模型输出中';
  return '候选预览生成中';
});
</script>

<style scoped>
.agent-stream-preview {
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border-radius: 8px;
  min-height: 80px;
}

.agent-stream-preview--llm {
  border-color: color-mix(in srgb, var(--color-accent) 30%, var(--border-color));
  background: color-mix(in srgb, var(--color-accent-soft) 50%, var(--bg-secondary));
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

.agent-stream-preview__text--llm {
  color: var(--color-text-dim);
  font-style: italic;
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

@media (prefers-reduced-motion: reduce) {
  .agent-stream-preview__cursor {
    animation: none;
  }
}
</style>
