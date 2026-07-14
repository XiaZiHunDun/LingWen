<!--
  CreatorMemoryPanel.vue — 记忆库独立工作区 Tab
-->
<template>
  <section
    v-show="pt.isWorkspaceColumnVisible('memory')"
    class="creator-column pixel-card"
    :class="{ 
      'creator-column--desk-drawer': pt.deskDrawerActive?.(),
      'creator-column--desk-drawer--open': pt.deskDrawerActive?.(),
    }"
    data-testid="column-memory"
    :id="pt.deskDrawerActive?.() ? 'creator-desk-drawer-panel-memory' : undefined"
    :role="pt.deskDrawerActive?.() ? 'dialog' : undefined"
    :aria-modal="pt.deskDrawerActive?.() ? 'true' : undefined"
    :aria-labelledby="pt.deskDrawerActive?.() ? 'desk-drawer-title-memory' : undefined"
  >
    <div v-if="pt.deskDrawerActive?.()" class="desk-drawer-chrome" data-testid="desk-drawer-chrome-memory">
      <h2 id="desk-drawer-title-memory" class="desk-drawer-chrome__title">记忆库</h2>
      <button
        type="button"
        class="mini-btn pixel-border"
        data-testid="desk-drawer-close-memory"
        aria-label="关闭记忆库抽屉"
        @click="pt.closeDeskDrawer()"
      >
        关闭
      </button>
    </div>
    <h2 v-else class="column-title">记忆库</h2>

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
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-md);
  font-size: var(--text-sm);
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
  border: var(--border-width) solid var(--border-color);
}

.memory-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: var(--space-md);
}

.filter-btn {
  font-size: var(--text-xs);
  padding: 6px 14px;
  cursor: pointer;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--bg-elevated);
  color: var(--color-text-secondary);
  transition: all 0.18s ease;
}

.filter-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: var(--color-accent-soft);
}

.filter-btn--active {
  background: var(--color-accent);
  color: #fff;
  border-color: var(--color-accent);
  font-weight: 600;
}

.memory-hint {
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 4px 12px;
  cursor: pointer;
  white-space: nowrap;
  border-radius: var(--radius-xs);
  transition: all 0.15s ease;
}

.mini-btn:hover:not(:disabled) {
  background: var(--bg-muted);
}

.mini-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.desk-drawer-chrome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  flex-shrink: 0;
}

.desk-drawer-chrome__title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: 700;
}
</style>
