<!-- dashboard/frontend/src/components/RippleCard.vue (NEW, Phase 9.13) -->
<template>
  <div
    class="ripple-card"
    :class="`ripple-card--${ripple.status}`"
    data-testid="ripple-card"
    @click="$emit('select', ripple)"
  >
    <div class="ripple-card__header">
      <span class="ripple-card__dim" :data-testid="`ripple-dim-${ripple.dimension}`">
        {{ ripple.dimension }}
      </span>
      <span
        class="ripple-card__status"
        :data-testid="`ripple-status`"
        :class="`ripple-card__status--${ripple.status}`"
      >
        {{ ripple.status }}
      </span>
    </div>
    <div class="ripple-card__body">
      <span class="ripple-card__rel">{{ ripple.relationship_type }}</span>
      <span class="ripple-card__refs">
        ch{{ ripple.source_chapter }} → ch{{ ripple.target_chapter }}
      </span>
    </div>
    <div class="ripple-card__footer">
      <span class="ripple-card__confidence" data-testid="ripple-confidence">
        confidence {{ ripple.confidence }}/5
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  ripple: { type: Object, required: true },
});
defineEmits(['select']);
</script>

<style scoped>
.ripple-card {
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 8px;
  cursor: pointer;
  background: #fff;
  transition: background 0.15s;
}
.ripple-card:hover { background: #f6f6f6; }
.ripple-card__header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.ripple-card__dim { font-weight: 600; color: #2c3e50; }
.ripple-card__status { font-size: 0.85em; padding: 2px 8px; border-radius: 4px; }
.ripple-card__status--pending { background: #fff3cd; color: #856404; }
.ripple-card__status--applied { background: #d4edda; color: #155724; }
.ripple-card__status--rejected { background: #f8d7da; color: #721c24; }
.ripple-card__body { display: flex; gap: 12px; font-size: 0.9em; color: #555; }
.ripple-card__footer { margin-top: 6px; font-size: 0.85em; color: #888; }
</style>
