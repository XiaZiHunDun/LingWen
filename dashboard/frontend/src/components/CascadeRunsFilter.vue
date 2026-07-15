<!-- dashboard/frontend/src/components/CascadeRunsFilter.vue (NEW, Phase 9.23 T4) -->
<!-- Per-ripple Cascade runs filter bar: 3 dropdowns + 2 number inputs + conditional
  Reset button. v-model 风格 (modelValue + update:modelValue). 0 fetch / 0 router
  push (parent 负责 URL sync + fetch, 单向数据流). 复 Phase 9.13 RippleFilter.vue
  风格 + 1:1 testid-class-sync convention. -->
<template>
  <div class="cascade-runs-filter" data-testid="cascade-runs-filter">
    <label class="cascade-runs-filter-label filter-status-label">
      Status:
      <select
        :value="modelValue.status"
        @change="emitChange('status', $event.target.value)"
        data-testid="filter-status"
        class="filter-status"
      >
        <option value="all">all</option>
        <option value="running">running</option>
        <option value="completed">completed</option>
        <option value="cancelled">cancelled</option>
        <option value="failed">failed</option>
      </select>
    </label>

    <label class="cascade-runs-filter-label filter-depth-label">
      Depth:
      <input
        type="number" min="1" max="10"
        :value="modelValue.minDepth ?? ''"
        placeholder="min"
        @input="emitNumber('minDepth', $event.target.value)"
        data-testid="filter-min-depth"
        class="filter-min-depth"
      />
      <span class="filter-depth-sep">–</span>
      <input
        type="number" min="1" max="10"
        :value="modelValue.maxDepth ?? ''"
        placeholder="max"
        @input="emitNumber('maxDepth', $event.target.value)"
        data-testid="filter-max-depth"
        class="filter-max-depth"
      />
    </label>

    <label class="cascade-runs-filter-label filter-algorithm-label">
      Algorithm:
      <select
        :value="modelValue.algorithm"
        @change="emitChange('algorithm', $event.target.value)"
        data-testid="filter-algorithm"
        class="filter-algorithm"
      >
        <option value="all">all</option>
        <option value="v1">v1</option>
        <option value="v2_weighted">v2_weighted</option>
      </select>
    </label>

    <label v-if="globalMode" class="cascade-runs-filter-label filter-ripple-label">
      Ripple:
      <input
        type="text"
        :value="modelValue.rippleId ?? ''"
        placeholder="ripple id"
        data-testid="filter-ripple-id"
        class="filter-ripple-id"
        @input="emitChange('rippleId', $event.target.value)"
      />
    </label>

    <label v-if="globalMode" class="cascade-runs-filter-label filter-since-label">
      Since (days):
      <input
        type="number" min="1" max="3650"
        :value="modelValue.sinceDays ?? ''"
        placeholder="all"
        data-testid="filter-since-days"
        class="filter-since-days"
        @input="emitSinceDays($event.target.value)"
      />
    </label>

    <button
      v-if="hasActiveFilter"
      type="button"
      @click="emit('update:modelValue', defaultFilters())"
      data-testid="filter-reset"
      class="filter-reset"
    >Reset</button>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  globalMode: { type: Boolean, default: false },
  modelValue: {
    type: Object,
    required: true,
    validator: (v) => ['status', 'minDepth', 'maxDepth', 'algorithm'].every((k) => k in v),
  },
});
const emit = defineEmits(['update:modelValue']);

function defaultFilters() {
  return {
    status: 'all',
    minDepth: null,
    maxDepth: null,
    algorithm: 'all',
    rippleId: '',
    sinceDays: null,
  };
}

const hasActiveFilter = computed(() =>
  props.modelValue.status !== 'all' ||
  props.modelValue.minDepth != null ||
  props.modelValue.maxDepth != null ||
  props.modelValue.algorithm !== 'all' ||
  (props.globalMode && props.modelValue.rippleId) ||
  (props.globalMode && props.modelValue.sinceDays != null)
);

function emitChange(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}

function emitNumber(key, raw) {
  const n = raw === '' ? null : Number(raw);
  // Defensive: ignore NaN / out-of-range (parent's debounce + URL parser handle too)
  if (n !== null && (!Number.isFinite(n) || n < 1 || n > 10)) return;
  emit('update:modelValue', { ...props.modelValue, [key]: n });
}

function emitSinceDays(raw) {
  const n = raw === '' ? null : Number(raw);
  if (n !== null && (!Number.isFinite(n) || n < 1 || n > 3650)) return;
  emit('update:modelValue', { ...props.modelValue, sinceDays: n });
}
</script>

<style scoped>
.cascade-runs-filter {
  display: flex; gap: 16px; margin-bottom: 12px; align-items: center;
  flex-wrap: wrap; font-size: var(--text-sm); font-family: var(--font-ui);
}
.cascade-runs-filter-label { display: flex; align-items: center; gap: 8px; font-size: var(--text-sm); }
.cascade-runs-filter select, .cascade-runs-filter input {
  padding: 8px 10px; min-height: 36px; border-radius: 4px; border: 1px solid #ccc;
  font-size: var(--text-sm); font-family: var(--font-ui);
}
.cascade-runs-filter input[type="number"] { width: 60px; }
.cascade-runs-filter input[type="text"] { width: 120px; }
.filter-depth-sep { color: #666; }
.filter-reset {
  padding: 8px 12px; border: 1px solid #c0392b; background: #fff; color: #c0392b;
  border-radius: 4px; cursor: pointer; font-size: var(--text-sm); font-family: var(--font-ui);
}
.filter-reset:hover { background: #c0392b; color: #fff; }
</style>
