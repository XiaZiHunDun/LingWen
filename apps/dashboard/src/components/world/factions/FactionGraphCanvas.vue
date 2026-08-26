<!--
  FactionGraphCanvas.vue — Phase 117 (Task 16) 势力关系图画布 stub
  完整 cytoscape graph 实现在 Task 17,本任务仅交付 stub 占位.
-->
<template>
  <div data-testid="faction-graph-canvas-stub" class="faction-graph-canvas-stub world-stub">
    势力关系图 (Phase 117 Task 17 follow-up)
  </div>
</template>

<script setup>
defineProps({
  factions: { type: Array, required: true },
  relationships: { type: Array, required: true },
})
</script>

<style scoped>
.world-stub {
  padding: var(--space-md);
  color: var(--color-text-dim);
  font-size: var(--text-sm);
}
</style>