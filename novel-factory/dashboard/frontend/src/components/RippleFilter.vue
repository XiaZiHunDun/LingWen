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
});
defineEmits(['update:status', 'update:dimension', 'update:volume']);
</script>

<style scoped>
.ripple-filter { display: flex; gap: 16px; margin-bottom: 16px; }
.ripple-filter label { display: flex; align-items: center; gap: 6px; font-size: 0.9em; }
.ripple-filter select { padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; }
</style>
