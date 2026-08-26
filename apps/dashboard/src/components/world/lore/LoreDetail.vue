<!--
  LoreDetail.vue — Phase 117 (Task 19) 世界书详情侧栏
  纯展示选中 lore (title / category / body),由父级 LoreList 控制 selected.
  通过 emit('close') 由父级关闭.
-->
<template>
  <aside class="lore-detail lore-detail-panel" data-testid="lore-detail">
    <button
      type="button"
      class="lore-detail__close lore-detail-close"
      data-testid="lore-detail-close"
      @click="$emit('close')"
    >关闭</button>
    <h2 class="lore-detail__title">{{ lore.title }}</h2>
    <p class="lore-detail__category lore-detail-category" data-testid="lore-detail-category">
      {{ lore.category }}
    </p>
    <pre class="lore-detail__body lore-detail-body" data-testid="lore-detail-body">{{ lore.body }}</pre>
    <button
      type="button"
      class="lore-detail-edit-toggle lore-detail__edit-toggle"
      data-testid="lore-detail-edit-toggle"
      @click="editing = !editing"
    >{{ editing ? '取消新增' : '新增条目' }}</button>
    <LoreEditor v-if="editing" />
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import LoreEditor from './LoreEditor.vue'

defineProps({
  /** @type {{ id: number, slug: string, title: string, category: string, summary?: string|null, body: string }} */
  lore: { type: Object, required: true },
})
defineEmits(['close'])

const editing = ref(false)
</script>

<style scoped>
.lore-detail,
.lore-detail-panel {
  position: sticky;
  top: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: var(--color-surface, transparent);
}
.lore-detail__close,
.lore-detail-close {
  align-self: flex-end;
  background: transparent;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font: inherit;
  color: inherit;
  padding: 0.125rem 0.5rem;
}
.lore-detail__title {
  margin: 0;
  font-size: var(--text-lg);
}
.lore-detail__category,
.lore-detail-category {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.75;
}
.lore-detail__body,
.lore-detail-body {
  margin: 0;
  font-family: inherit;
  font-size: var(--text-sm);
  white-space: pre-wrap;
  word-break: break-word;
}
.lore-detail-edit-toggle,
.lore-detail__edit-toggle {
  align-self: flex-start;
  background: transparent;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font: inherit;
  color: inherit;
  padding: 0.125rem 0.5rem;
}
</style>