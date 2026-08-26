<!--
  LoreList.vue — Phase 117 (Task 19) 世界书列表 + 分类筛选
  通过 useWorldDb().listLore(category) 拉取 lore 条目,按分类过滤.
  点击条目打开 LoreDetail 侧栏 (本地 selected state).
-->
<template>
  <div class="lore-list" data-testid="lore-list">
    <div class="lore-list__categories lore-categories" data-testid="lore-categories">
      <button
        v-for="cat in categories"
        :key="cat"
        type="button"
        class="lore-list__category lore-category-btn"
        :class="{ 'is-active': filter === cat }"
        :data-testid="`lore-category-${cat}`"
        @click="toggleFilter(cat)"
      >{{ cat }}</button>
    </div>
    <ul class="lore-list__items lore-list-items" data-testid="lore-list-items">
      <li
        v-for="l in lore"
        :key="l.id"
        class="lore-item lore-item-row"
        :data-testid="`lore-item-${l.slug}`"
        @click="open(l)"
      >
        <strong class="lore-item__title">{{ l.title }}</strong>
        <span class="lore-item__category">{{ l.category }}</span>
      </li>
    </ul>
    <p v-if="lore.length === 0" class="lore-list__empty lore-list-empty" data-testid="lore-list-empty">
      暂无条目
    </p>
    <LoreDetail v-if="selected" :lore="selected" @close="selected = null" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useWorldDb } from '@/composables/world/useWorldDb.js'
import LoreDetail from './LoreDetail.vue'

const { listLore } = useWorldDb()
const lore = ref([])
const filter = ref(null)
const selected = ref(null)
const categories = ['magic_system', 'geography', 'history', 'creature', 'technology']

function toggleFilter(cat) {
  filter.value = filter.value === cat ? null : cat
}

async function refresh() {
  lore.value = await listLore(filter.value || undefined)
}

function open(l) { selected.value = l }

watch(filter, () => { refresh() })

onMounted(refresh)
</script>

<style scoped>
.lore-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.lore-list__categories,
.lore-categories {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}
.lore-list__category,
.lore-category-btn {
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-size: var(--text-sm);
}
.lore-list__category.is-active,
.lore-category-btn.is-active {
  background: var(--bg-muted, transparent);
  font-weight: 600;
}
.lore-list__items,
.lore-list-items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.lore-item,
.lore-item-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-sm);
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, currentColor);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
}
.lore-item:hover,
.lore-item-row:hover {
  background: var(--bg-muted, transparent);
}
.lore-item__title {
  flex: 1;
}
.lore-item__category {
  font-size: var(--text-xs);
  opacity: 0.7;
}
.lore-list__empty,
.lore-list-empty {
  margin: 0;
  font-size: var(--text-sm);
  opacity: 0.7;
}
</style>