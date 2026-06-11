<!-- Phase 9.46 F35: Global cascade runs page (cross-ripple view) -->
<template>
  <div class="cascade-runs-page" data-testid="cascade-runs-page">
    <header class="page-header">
      <h2 class="page-title">Cascade Runs</h2>
      <p class="page-subtitle">跨 ripple 历史 cascade 运行记录</p>
    </header>
    <CascadeRunsPanel global-mode />
  </div>
</template>

<script setup>
import CascadeRunsPanel from '../components/CascadeRunsPanel.vue';
</script>

<style scoped>
.cascade-runs-page {
  padding: var(--space-md);
}
.page-header {
  margin-bottom: var(--space-md);
}
.page-title {
  font-size: 14px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-accent);
  margin: 0 0 var(--space-sm) 0;
}
.page-subtitle {
  font-size: 10px;
  color: var(--color-text);
  opacity: 0.7;
  margin: 0;
}
</style>
