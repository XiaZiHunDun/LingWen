<template>
  <nav class="hub-tab-bar" :data-testid="testId">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="hub-tab pixel-border"
      :class="{ 'hub-tab--active': modelValue === tab.id }"
      :data-testid="`${testId}-${tab.id}`"
      @click="$emit('update:modelValue', tab.id)"
    >
      <span v-if="tab.icon" class="hub-tab-icon">{{ tab.icon }}</span>
      {{ tab.label }}
      <span v-if="badges?.[tab.id]" class="hub-tab-badge">{{ badges[tab.id] }}</span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
  testId: { type: String, default: 'hub-tabs' },
  badges: { type: Object, default: null },
});

defineEmits(['update:modelValue']);
</script>

<style scoped>
.hub-tab-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.hub-tab {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  font-weight: 500;
  padding: 10px 16px;
  background: var(--bg-secondary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.1s ease;
}

.hub-tab:hover:not(.hub-tab--active) {
  background: var(--bg-primary);
  transform: translateY(-1px);
}

.hub-tab--active {
  background: var(--color-accent);
  color: white;
}

.hub-tab-icon {
  font-size: 12px;
}

.hub-tab-badge {
  font-size: var(--text-xs);
  background: rgba(0, 0, 0, 0.15);
  padding: 1px 6px;
  border-radius: 10px;
}
</style>
