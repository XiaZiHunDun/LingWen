<!-- dashboard/frontend/src/components/RippleList.vue (NEW, Phase 9.13) -->
<template>
  <div class="ripple-list">
    <div v-if="loading" data-testid="ripple-list-loading" class="ripple-list__loading ripple-list-loading">
      加载中...
    </div>
    <div v-else-if="ripples.length === 0" data-testid="ripple-list-empty" class="ripple-list__empty ripple-list-empty">
      No ripples match current filter.
    </div>
    <RippleCard
      v-for="ripple in ripples"
      :key="ripple.ripple_id"
      :ripple="ripple"
      @select="(r) => $emit('select', r)"
    />
  </div>
</template>

<script setup>
import RippleCard from './RippleCard.vue';
defineProps({
  ripples: { type: Array, required: true },
  loading: { type: Boolean, default: false },
});
defineEmits(['select']);
</script>

<style scoped>
.ripple-list__loading, .ripple-list__empty {
  padding: 24px;
  text-align: center;
  color: #888;
  background: #f9f9f9;
  border-radius: 6px;
}
</style>
