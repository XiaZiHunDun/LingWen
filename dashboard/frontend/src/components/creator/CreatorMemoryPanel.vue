<template>
  <section
    v-show="pt.isWorkspaceColumnVisible('memory')"
    class="creator-column"
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
    <div class="memory-desk">
      <div class="memory-desk__hero">
        <p class="memory-desk__intro">查看和搜索故事中的人物、片段、伏笔等记忆</p>
      </div>

      <div class="memory-desk__content">
        <div class="memory-search-wrapper">
          <CreatorMemorySearch />
        </div>

        <div class="memory-filters">
          <button
            v-for="f in filters"
            :key="f.id"
            type="button"
            class="filter-btn"
            :class="{ 'filter-btn--active': pt.memoryFilter === f.id }"
            :data-testid="`memory-filter-${f.id}`"
            @click="pt.memoryFilter = f.id"
          >
            {{ f.icon }} {{ f.label }}
          </button>
        </div>

        <div class="memory-assets-wrapper">
          <CreatorMemoryAssetsPanel compact />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_PRODUCT_TOOLS_KEY } from './creatorProductToolsKey.js';
import CreatorMemoryAssetsPanel from './CreatorMemoryAssetsPanel.vue';
import CreatorMemorySearch from './CreatorMemorySearch.vue';

const pt = inject(CREATOR_PRODUCT_TOOLS_KEY);

const filters = [
  { id: 'all', label: '全部', icon: '📋' },
  { id: 'character', label: '角色', icon: '👤' },
  { id: 'memory', label: '片段', icon: '📝' },
  { id: 'foreshadow', label: '伏笔', icon: '🔮' },
  { id: 'setting', label: '设定', icon: '🌍' },
];
</script>

<style scoped>
.creator-column {
  padding: 0;
  min-height: 0;
  border: none;
  background: transparent;
  box-shadow: none;
}

.memory-desk {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.memory-desk__hero {
  flex-shrink: 0;
  padding: var(--space-md) var(--space-lg);
  border-bottom: var(--border-width) solid var(--border-color);
  background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-elevated) 100%);
}

.memory-desk__intro {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.memory-desk__content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.memory-search-wrapper {
  flex-shrink: 0;
}

.memory-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex-shrink: 0;
}

.filter-btn {
  font-size: var(--text-xs);
  padding: 6px 12px;
  cursor: pointer;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--bg-primary);
  color: var(--color-text-secondary);
  transition: all 0.18s ease;
}

.filter-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.filter-btn--active {
  background: var(--color-accent);
  color: #fff;
  border-color: var(--color-accent);
  font-weight: 600;
}

.memory-assets-wrapper {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.mini-btn {
  font-size: var(--text-xs);
  padding: 4px 10px;
  cursor: pointer;
  border-radius: var(--radius-xs);
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
