<template>
  <div class="stat-card pixel-border">
    <span class="stat-label">{{ label }}</span>
    <span class="stat-value">{{ value }}</span>
    <span v-if="trend !== undefined" class="stat-trend" :class="trendClass">
      {{ trend >= 0 ? '+' : '' }}{{ trend }}%
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  trend: {
    type: Number,
    default: undefined
  }
})

const trendClass = computed(() => {
  if (props.trend === undefined) return ''
  return props.trend >= 0 ? 'trend-positive' : 'trend-negative'
})
</script>

<style scoped>
.stat-card {
  background-color: var(--bg-secondary);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  min-width: 120px;
}

.stat-label {
  font-size: 8px;
  color: var(--color-text);
  opacity: 0.8;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: var(--color-text);
}

.stat-trend {
  font-size: 8px;
  font-weight: bold;
}

.trend-positive {
  color: var(--color-success);
}

.trend-negative {
  color: var(--color-danger);
}
</style>