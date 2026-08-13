<!-- Phase 9.46 F35: Global cascade runs page (cross-ripple view) -->
<template>
  <div class="cascade-runs-page" data-testid="cascade-runs-page">
    <header class="page-header">
      <h2 class="page-title">级联运行</h2>
      <p class="page-subtitle">跨涟漪的历史级联执行记录</p>
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
  font-size: var(--text-xl);
  font-family: var(--font-ui);
  font-weight: 700;
  color: var(--color-accent);
  margin: 0 0 var(--space-sm) 0;
}
.page-subtitle {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text-dim);
  margin: 0;
}
</style>
