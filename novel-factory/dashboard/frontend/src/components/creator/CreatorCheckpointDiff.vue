<!--
  CreatorCheckpointDiff.vue — checkpoint 与当前正文行级对比
-->
<template>
  <div
    v-if="diffView"
    class="checkpoint-diff pixel-border"
    data-testid="write-checkpoint-diff"
  >
    <div class="checkpoint-diff__head">
      <strong>版本对比 · {{ diffView.checkpoint.label }}</strong>
      <span class="meta-line">{{ diffView.changeCount }} 处变化</span>
      <button type="button" class="mini-btn pixel-border" data-testid="checkpoint-diff-close" @click="$emit('close')">
        关闭
      </button>
    </div>
    <div class="checkpoint-diff__panes">
      <div class="checkpoint-diff__pane">
        <p class="checkpoint-diff__pane-title">回滚点</p>
        <pre class="checkpoint-diff__text">{{ diffView.checkpoint.bodySnapshot }}</pre>
      </div>
      <div class="checkpoint-diff__pane">
        <p class="checkpoint-diff__pane-title">当前草稿</p>
        <pre class="checkpoint-diff__lines">
          <span
            v-for="(line, idx) in diffView.lines"
            :key="idx"
            class="checkpoint-diff__line"
            :class="`checkpoint-diff__line--${line.type}`"
          >{{ linePrefix(line) }}{{ line.text }}</span>
        </pre>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  diffView: { type: Object, default: null },
});

defineEmits(['close']);

function linePrefix(line) {
  if (line.type === 'add') return '+ ';
  if (line.type === 'remove') return '- ';
  return '  ';
}
</script>

<style scoped>
.checkpoint-diff {
  padding: var(--space-sm);
  margin-top: var(--space-xs);
  background: var(--bg-primary);
}
.checkpoint-diff__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  margin-bottom: var(--space-sm);
}
.checkpoint-diff__panes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-sm);
}
@media (max-width: 720px) {
  .checkpoint-diff__panes {
    grid-template-columns: 1fr;
  }
}
.checkpoint-diff__pane-title {
  font-size: var(--text-xs);
  margin: 0 0 4px;
  color: var(--color-text-dim);
}
.checkpoint-diff__text,
.checkpoint-diff__lines {
  font-size: 10px;
  white-space: pre-wrap;
  max-height: 160px;
  overflow: auto;
  margin: 0;
  padding: var(--space-xs);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
}
.checkpoint-diff__line {
  display: block;
}
.checkpoint-diff__line--add {
  background: rgba(80, 180, 100, 0.15);
}
.checkpoint-diff__line--remove {
  background: rgba(200, 80, 80, 0.12);
  text-decoration: line-through;
  opacity: 0.75;
}
.meta-line {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
  margin-left: auto;
}
</style>
