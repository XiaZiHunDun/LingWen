<template>
  <div class="stats-widget">
    <div class="widget-header">
      <h3 class="widget-title">{{ title }}</h3>
      <button v-if="refreshable" class="refresh-btn" @click="$emit('refresh')">
        ↻
      </button>
    </div>
    <div class="stats-grid">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="stat-item stat-card"
        data-testid="stat-card"
      >
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
        <div v-if="stat.trend" class="stat-trend" :class="stat.trend >= 0 ? 'up' : 'down'">
          {{ stat.trend >= 0 ? '↑' : '↓' }} {{ Math.abs(stat.trend) }}%
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '统计数据' },
  stats: { type: Array, default: () => [] },
  refreshable: { type: Boolean, default: false },
})

defineEmits(['refresh'])
</script>

<style scoped>
.stats-widget {
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

.refresh-btn {
  background: none;
  border: none;
  font-size: var(--text-lg);
  cursor: pointer;
  color: var(--color-text-dim);
  transition: color 0.2s;
}

.refresh-btn:hover {
  color: var(--color-accent);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--space-sm);
}

.stat-item {
  text-align: center;
  padding: var(--space-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: bold;
  color: var(--color-text);
  font-family: var(--font-mono);
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  margin-top: 2px;
}

.stat-trend {
  font-size: var(--text-xs);
  margin-top: 4px;
  font-family: var(--font-mono);
}

.stat-trend.up {
  color: var(--color-success);
}

.stat-trend.down {
  color: var(--color-danger);
}
</style>
