<!--
  CreatorMemoryPanel.vue — 记忆库独立工作区 Tab
-->
<template>
  <section
    v-show="pt.isWorkspaceColumnVisible('memory')"
    class="creator-column pixel-card"
    data-testid="column-memory"
  >
    <h2 class="column-title">记忆库</h2>

    <div class="memory-status pixel-border" data-testid="memory-status-bar">
      <span class="meta-line">
        RAG：{{ pt.memoryRagEnabled ? '已启用' : '已关闭' }}
        · 记忆系统：{{ pt.memoryAvailable ? '已连接' : '离线/降级' }}
      </span>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="memory-refresh-btn"
        :disabled="pt.memoryAssetsLoading"
        @click="pt.loadMemoryAssets"
      >
        {{ pt.memoryAssetsLoading ? '刷新中…' : '刷新' }}
      </button>
    </div>

    <CreatorMemorySearch />

    <div class="memory-filters" data-testid="memory-filters">
      <button
        v-for="f in filters"
        :key="f.id"
        type="button"
        class="filter-btn pixel-border"
        :class="{ 'filter-btn--active': pt.memoryFilter === f.id }"
        :data-testid="`memory-filter-${f.id}`"
        @click="pt.memoryFilter = f.id"
      >
        {{ f.label }}
      </button>
    </div>

    <CreatorMemoryAssetsPanel full />

    <p class="meta-line memory-hint">
      在「设定 → 创作偏好」中调整记忆 Top-K；向量不可用时自动本地匹配。
    </p>
  </section>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';
import CreatorMemoryAssetsPanel from './CreatorMemoryAssetsPanel.vue';
import CreatorMemorySearch from './CreatorMemorySearch.vue';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);

const filters = [
  { id: 'all', label: '全部' },
  { id: 'character', label: '角色' },
  { id: 'memory', label: '片段' },
  { id: 'foreshadow', label: '伏笔' },
  { id: 'setting', label: '设定' },
  { id: 'summary', label: '卷摘要' },
];
</script>

<style scoped>
.memory-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  margin-bottom: var(--space-sm);
  font-size: var(--text-sm);
}

.memory-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--space-sm);
}

.filter-btn {
  font-size: var(--text-xs);
  padding: 2px 8px;
  cursor: pointer;
}

.filter-btn--active {
  background: var(--color-accent-soft);
}

.memory-hint {
  margin-top: var(--space-md);
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 2px 8px;
  cursor: pointer;
  white-space: nowrap;
}
</style>
