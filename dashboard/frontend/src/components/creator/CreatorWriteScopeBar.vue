<!--
  CreatorWriteScopeBar.vue — 写作导演：当前作用域
-->
<template>
  <div class="write-scope-bar" data-testid="write-scope-bar">
    <template v-if="humanFirst">
      <strong class="write-scope-bar__value" data-testid="write-scope-human-label">{{ humanLabel }}</strong>
      <span v-if="humanHint" class="meta-line">{{ humanHint }}</span>
    </template>
    <template v-else>
      <span class="write-scope-bar__label">作用域</span>
      <strong class="write-scope-bar__value">{{ scope.label }}</strong>
      <span v-if="scope.type === 'selection'" class="meta-line">导演将针对选中段落给路径</span>
      <span v-else-if="scope.type === 'chapter'" class="meta-line">未选区时作用于整章</span>
      <span v-else class="meta-line write-scope-bar__hint">请选章或拖选正文段落</span>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  scope: { type: Object, required: true },
  humanFirst: { type: Boolean, default: false },
});

const humanLabel = computed(() => {
  const { scope } = props;
  if (scope.type === 'selection') {
    const len = scope.selection?.text?.length ?? 0;
    return `正在改：选中 ${len} 字`;
  }
  if (scope.type === 'chapter' && scope.chapter != null) {
    return `正在写：第 ${scope.chapter} 章`;
  }
  return '先选一章开始写';
});

const humanHint = computed(() => {
  if (props.scope.type === 'selection') return 'AI 建议将针对这段文字';
  if (props.scope.type === 'chapter') return null;
  return '在左侧点选章节';
});
</script>

<style scoped>
.write-scope-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs) var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-sm);
}
.write-scope-bar__label {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
.write-scope-bar__hint {
  color: #a60;
}
.meta-line {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
</style>
