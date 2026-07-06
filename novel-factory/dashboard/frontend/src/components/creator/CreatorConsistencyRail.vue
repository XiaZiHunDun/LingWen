<!--
  CreatorConsistencyRail.vue — 写作现场一致性侧栏
-->
<template>
  <div
    class="consistency-rail"
    :class="{ 'consistency-rail--nested': hideTitle }"
    data-testid="write-consistency-rail"
  >
    <p v-if="!hideTitle" class="consistency-rail__title">本章一致性</p>
    <ul v-if="items.length" class="consistency-rail__list">
      <li
        v-for="item in items"
        :key="item.id"
        class="consistency-rail__item"
        :class="`consistency-rail__item--${item.level}`"
        :data-testid="`consistency-item-${item.kind}`"
      >
        {{ item.text }}
      </li>
    </ul>
    <p v-else class="meta-line">暂无冲突或偏离标记</p>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  hideTitle: { type: Boolean, default: false },
});
</script>

<style scoped>
.consistency-rail {
  padding: var(--space-sm);
  font-size: var(--text-xs);
}
.consistency-rail--nested {
  padding: 0;
}
.consistency-rail__title {
  font-weight: 600;
  margin: 0 0 var(--space-xs);
}
.consistency-rail__list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.consistency-rail__item {
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
}
.consistency-rail__item--warn { color: #a60; }
.consistency-rail__item--info { color: var(--color-text-dim); }
.consistency-rail__item--ok { color: var(--color-text-dim); }
.meta-line {
  margin: 0;
  color: var(--color-text-dim);
}
</style>
