<!-- dashboard/frontend/src/components/RippleFilter.vue (NEW, Phase 9.13) -->
<template>
  <div class="ripple-filter">
    <label>
      Status:
      <select
        :value="status"
        class="ripple-filter-status"
        data-testid="ripple-filter-status"
        @change="$emit('update:status', $event.target.value)"
      >
        <option value="all">all</option>
        <option value="pending">pending</option>
        <option value="confirmed">confirmed</option>
        <option value="applied">applied</option>
        <option value="rejected">rejected</option>
        <option value="failed">failed</option>
      </select>
    </label>
    <label>
      Dimension:
      <select
        :value="dimension"
        class="ripple-filter-dimension"
        data-testid="ripple-filter-dimension"
        @change="$emit('update:dimension', $event.target.value)"
      >
        <option value="all">all</option>
        <option value="character">character</option>
        <option value="foreshadow">foreshadow</option>
        <option value="setting">setting</option>
        <option value="plot_point">plot_point</option>
      </select>
    </label>
    <label>
      Sort:
      <select
        :value="sortBy"
        class="ripple-filter-sort"
        data-testid="ripple-filter-sort"
        @change="$emit('update:sortBy', $event.target.value)"
      >
        <option value="created_at">newest</option>
        <option value="impact_score">impact score</option>
      </select>
    </label>
    <label>
      Min score:
      <input
        type="number"
        min="0"
        step="0.1"
        :value="minScore"
        class="ripple-filter-min-score"
        data-testid="ripple-filter-min-score"
        @input="$emit('update:minScore', $event.target.value)"
      />
    </label>
    <label>
      Volume:
      <select
        :value="volume"
        class="ripple-filter-volume"
        data-testid="ripple-filter-volume"
        @change="$emit('update:volume', $event.target.value)"
      >
        <option value="all">all</option>
        <option value="1">vol 1</option>
        <option value="2">vol 2</option>
        <option value="3">vol 3</option>
      </select>
    </label>
  </div>
</template>

<script setup>
defineProps({
  status: { type: String, default: 'all' },
  dimension: { type: String, default: 'all' },
  volume: { type: String, default: 'all' },
  sortBy: { type: String, default: 'created_at' },
  minScore: { type: String, default: '' },
});
defineEmits(['update:status', 'update:dimension', 'update:volume', 'update:sortBy', 'update:minScore']);
</script>

<style scoped>
.ripple-filter { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 16px; font-size: var(--text-sm); }
.ripple-filter label { display: flex; align-items: center; gap: 8px; font-size: var(--text-sm); font-family: var(--font-ui); }
.ripple-filter select, .ripple-filter input { padding: 8px 10px; min-height: 36px; border-radius: 4px; border: 1px solid #ccc; font-size: var(--text-sm); }
</style>
