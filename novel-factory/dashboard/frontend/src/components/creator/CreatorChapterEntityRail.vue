<!--
  CreatorChapterEntityRail.vue — 写栏本章相关实体卡
-->
<template>
  <div
    class="chapter-entity-rail"
    :class="{ 'chapter-entity-rail--nested': hideTitle }"
    data-testid="write-chapter-entity-rail"
  >
    <p v-if="!hideTitle" class="chapter-entity-rail__title">本章实体</p>
    <p v-if="!entities.length" class="meta-line">选章后显示相关角色 / 伏笔 / 记忆片段</p>
    <ul v-else class="chapter-entity-rail__list">
      <li
        v-for="entity in entities"
        :key="entity.id"
        class="chapter-entity-rail__card"
        :data-testid="`chapter-entity-${entity.id}`"
      >
        <div class="chapter-entity-rail__head">
          <strong>{{ entity.name }}</strong>
          <span class="chapter-entity-rail__kind">{{ kindLabel(entity.kind) }}</span>
        </div>
        <p v-if="entity.excerpt" class="meta-line">{{ entity.excerpt }}</p>
        <p class="meta-line chapter-entity-rail__rel">
          {{ entity.relevance === 'chapter' ? '本章相关' : '正文提及' }}
        </p>
        <button
          type="button"
          class="link-btn meta-line"
          data-testid="chapter-entity-goto-memory"
          @click="goMemoryTab"
        >
          记忆库 →
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

defineProps({
  entities: { type: Array, default: () => [] },
  hideTitle: { type: Boolean, default: false },
});

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);

function kindLabel(kind) {
  if (kind === 'character') return '角色';
  if (kind === 'foreshadow') return '伏笔';
  return '记忆';
}

function goMemoryTab() {
  pt.setWorkspaceTab('memory');
}
</script>

<style scoped>
.chapter-entity-rail {
  padding: var(--space-sm);
  font-size: var(--text-xs);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
}
.chapter-entity-rail--nested {
  padding: 0;
  border: none;
  background: transparent;
}
.chapter-entity-rail__title {
  font-weight: 600;
  margin: 0 0 var(--space-xs);
}
.chapter-entity-rail__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.chapter-entity-rail__card {
  padding: var(--space-xs);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
}
.chapter-entity-rail__head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-xs);
}
.chapter-entity-rail__kind {
  color: var(--color-text-dim);
}
.meta-line {
  margin: 4px 0 0;
  color: var(--color-text-dim);
}
.link-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-decoration: underline;
  color: inherit;
  font: inherit;
}
</style>
