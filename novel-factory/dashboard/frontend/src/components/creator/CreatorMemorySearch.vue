<!--
  CreatorMemorySearch.vue — 记忆语义搜索（高亮 + 引用溯源）
-->
<template>
  <section class="memory-search pixel-border" data-testid="creator-memory-search">
    <h3 class="subsection-title">语义搜索</h3>
    <form class="memory-search-form" @submit.prevent="pt.runMemorySearch">
      <input
        v-model="pt.memorySearchQuery"
        type="search"
        class="vol-input memory-search-input"
        data-testid="memory-search-input"
        placeholder="例如：主角此刻在哪里？"
      >
      <select
        v-model="pt.memorySearchScope"
        class="vol-input"
        data-testid="memory-search-scope"
      >
        <option value="all">全部</option>
        <option value="character">角色</option>
        <option value="chapter">章节</option>
        <option value="relationship">关系</option>
      </select>
      <button
        type="submit"
        class="mini-btn pixel-border"
        data-testid="memory-search-btn"
        :disabled="pt.memorySearchBusy || !pt.memorySearchQuery.trim()"
      >
        {{ pt.memorySearchBusy ? '搜索中…' : '搜索' }}
      </button>
    </form>
    <p v-if="pt.memorySearchRan" class="meta-line" data-testid="memory-search-hint">
      <template v-if="pt.memorySearchUsedFallback">向量检索不可用，已使用本地匹配。</template>
      <template v-else-if="pt.memoryAvailable">向量检索结果。</template>
      <template v-else>本地匹配结果。</template>
      <span v-if="pt.memorySearchQuery"> · 关键词「{{ pt.memorySearchQuery }}」</span>
    </p>
    <ul v-if="pt.memorySearchResults.length" class="search-results">
      <li
        v-for="row in pt.memorySearchResults"
        :key="row.id"
        class="search-row"
        :data-testid="`memory-search-result-${row.id}`"
      >
        <div class="search-head">
          <span class="asset-kind">{{ row.kind }}</span>
          <span v-if="row.asset_name" class="asset-name">{{ row.asset_name }}</span>
          <span class="meta-line">score {{ row.score.toFixed(2) }}</span>
        </div>
        <p
          class="asset-excerpt"
          :data-testid="`memory-search-snippet-${row.id}`"
          v-html="pt.highlightMemorySnippet(row.snippet, row.matched_terms)"
        />
        <p class="citation-line" :data-testid="`memory-search-citation-${row.id}`">
          <span class="citation-label">溯源</span>
          {{ pt.formatMemoryCitation(row) }}
          <span class="source-tag">{{ row.source }}</span>
        </p>
        <div class="search-actions">
          <button
            v-if="row.chapter"
            type="button"
            class="link-btn"
            :data-testid="`memory-search-jump-${row.id}`"
            @click="pt.jumpToChapter(row.chapter)"
          >
            跳转第{{ row.chapter }}章
          </button>
          <button
            v-if="row.kind === 'setting' || row.kind === 'summary'"
            type="button"
            class="link-btn"
            :data-testid="`memory-search-settings-${row.id}`"
            @click="pt.setWorkspaceTab('settings')"
          >
            打开设定
          </button>
        </div>
      </li>
    </ul>
    <p
      v-else-if="pt.memorySearchRan && !pt.memorySearchBusy"
      class="meta-line"
      data-testid="memory-search-empty"
    >
      无匹配结果。
    </p>
  </section>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);
</script>

<style scoped>
.memory-search {
  padding: var(--space-sm);
  margin-bottom: var(--space-md);
}

.memory-search-form {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
  margin-bottom: var(--space-xs);
}

.memory-search-input {
  flex: 1 1 200px;
}

.search-results {
  list-style: none;
  padding: 0;
  margin: var(--space-sm) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.search-row {
  padding: var(--space-xs);
  border: 1px dashed #bbb;
  font-size: var(--text-sm);
}

.search-head {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  align-items: center;
}

.asset-kind,
.source-tag {
  font-size: var(--text-xs);
  padding: 1px 4px;
  background: rgba(0, 0, 0, 0.06);
}

.asset-name {
  font-weight: 600;
}

.asset-excerpt {
  margin: 4px 0;
  color: var(--text-muted, #666);
  line-height: 1.5;
}

.asset-excerpt :deep(mark.memory-hit) {
  background: #fff59d;
  padding: 0 2px;
}

.citation-line {
  margin: 0 0 4px;
  font-size: var(--text-xs);
  color: #555;
}

.citation-label {
  font-weight: 600;
  margin-right: 4px;
}

.search-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 8px;
  cursor: pointer;
}
</style>
