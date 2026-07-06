<!--
  CreatorChapterList.vue — 章节列表（写栏 / 工作台左栏复用）
-->
<template>
  <div
    v-if="!w.visibleChapters?.length"
    class="chapter-list-empty"
    data-testid="chapter-list-empty"
  >
    <p class="chapter-list-empty__title">还没有章节</p>
    <p class="meta-line">从第一章开始写，灵文会自动跟上你的节奏。</p>
    <button
      type="button"
      class="save-btn"
      data-testid="chapter-list-start-btn"
      @click="w.selectChapter(1)"
    >
      写第一章
    </button>
  </div>
  <template v-else>
    <ul
      class="chapter-list"
      :class="{ 'chapter-list--compact': compact }"
      data-testid="creator-chapter-list"
    >
      <li
        v-for="ch in w.visibleChapters"
        :key="ch.chapter"
        class="chapter-row"
        :class="[w.chapterRowClass(ch.chapter), { 'chapter-row--selected': w.selectedChapter === ch.chapter }]"
        role="button"
        tabindex="0"
        :data-testid="`chapter-row-${ch.chapter}`"
        :title="w.chapterRowTitle(ch.chapter)"
        @click="w.selectChapter(ch.chapter)"
        @keydown.enter="w.selectChapter(ch.chapter)"
      >
        <span class="ch-label">
          <span v-if="w.chapterVolumeLabel(ch.chapter)" class="ch-vol">{{ w.chapterVolumeLabel(ch.chapter) }} · </span>
          ch{{ String(ch.chapter).padStart(3, '0') }}
        </span>
        <span class="ch-status">
          {{ ch.has_body ? `${ch.word_count} 字` : (ch.has_outline ? '仅大纲' : '空') }}
        </span>
      </li>
    </ul>
    <p v-if="w.overview?.chapters?.length > 15" class="meta-line chapter-list__more">
      显示前 15 章 · 共 {{ w.overview.max_chapter }} 章上限
    </p>
  </template>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';

defineProps({
  compact: { type: Boolean, default: false },
});

const w = inject(CREATOR_WRITE_KEY);
</script>

<style scoped>
.chapter-list-empty {
  padding: var(--space-md);
  border: 1px dashed var(--border-color);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.chapter-list-empty__title {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.chapter-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chapter-list--compact {
  gap: 2px;
}

.chapter-row {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-sm);
  padding: 8px 10px;
  min-height: 40px;
  align-items: center;
  border: 1px solid var(--border-color);
  cursor: pointer;
}

.chapter-list--compact .chapter-row {
  padding: 4px 8px;
  min-height: 32px;
  font-size: var(--text-xs);
}

.chapter-row--selected {
  outline: 2px solid var(--color-accent);
}

.chapter-row--done {
  background: var(--color-success-soft);
}

.chapter-row--alert .ch-label::before {
  content: '● ';
  color: var(--color-danger);
}

.chapter-row--warn .ch-label::before {
  content: '● ';
  color: var(--color-warning, #aa8);
}

.ch-vol {
  color: var(--text-muted, var(--color-text-dim));
  font-size: var(--text-xs);
}

.chapter-list__more {
  margin: var(--space-xs) 0 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}

.meta-line {
  margin: 0;
}
</style>
