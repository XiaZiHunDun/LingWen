<!--
  CreatorBatchSummaryPrompt.vue — Batch 完成后的卷摘要提示（从 CreatorPage 拆出）
-->
<template>
  <div
    v-if="prompt"
    class="batch-summary-prompt pixel-border"
    data-testid="batch-summary-prompt"
  >
    <p>
      Batch 已完成 · 已生成 ch{{ formatChapter(prompt.start) }}–ch{{ formatChapter(prompt.end) }}
      卷摘要，请在下方查看脉络是否跑偏。
    </p>
    <p
      v-if="uiProfile.batch_deviation_prompt && prompt.alert_volume_labels?.length"
      class="meta-line batch-alert-volumes"
      data-testid="batch-alert-volumes-line"
    >
      以下卷需关注：{{ prompt.alert_volume_labels.join('、') }}
    </p>
    <button
      type="button"
      class="save-btn pixel-border"
      data-testid="open-batch-summary-btn"
      @click="$emit('open-summary', prompt.start, prompt.end)"
    >
      查看卷摘要
    </button>
    <button
      type="button"
      class="save-btn pixel-border"
      data-testid="dismiss-batch-summary-prompt-btn"
      @click="$emit('dismiss')"
    >
      知道了
    </button>
  </div>
</template>

<script setup>
defineProps({
  prompt: { type: Object, default: null },
  uiProfile: { type: Object, required: true },
});

defineEmits(['open-summary', 'dismiss']);

function formatChapter(n) {
  return String(n).padStart(3, '0');
}
</script>

<style scoped>
.batch-summary-prompt {
  margin: var(--space-sm) 0;
  padding: var(--space-sm);
}

.batch-alert-volumes {
  color: #a60;
}

.save-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
  margin-right: var(--space-xs);
  margin-top: var(--space-xs);
}

.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}
</style>
