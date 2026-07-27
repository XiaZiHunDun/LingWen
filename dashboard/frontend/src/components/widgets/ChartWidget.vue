<template>
  <div class="chart-widget">
    <div class="widget-header">
      <h3 class="widget-title">{{ title }}</h3>
      <div v-if="chartType" class="chart-type">{{ chartType }}</div>
    </div>
    <div class="chart-container">
      <slot name="chart">
        <div class="chart-placeholder">图表内容</div>
      </slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '图表' },
  chartType: { type: String, default: '' },
})
</script>

<style scoped>
.chart-widget {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  height: 100%;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.widget-title {
  font-size: var(--text-md);
  font-weight: bold;
  color: var(--color-text);
  font-family: var(--font-ui);
}

.chart-type {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  background: var(--bg-primary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.chart-container {
  height: calc(100% - 40px);
  min-height: 200px;
}

.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-dim);
  font-size: var(--text-sm);
}
</style>
