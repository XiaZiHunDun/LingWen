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
      <span
        v-if="ripple.impact_score != null"
        class="ripple-card__score ripple-impact-score"
        data-testid="ripple-impact-score"
      >
        impact {{ ripple.impact_score }}
      </span>
      <span
        v-if="ripple.parent_ripple_id"
        class="ripple-card__parent"
        data-testid="ripple-parent-badge"
      >
        child of {{ ripple.parent_ripple_id.slice(0, 8) }}
      </span>
      <span
        v-if="ripple.child_count > 0"
        class="ripple-card__children"
        data-testid="ripple-child-count"
      >
        {{ ripple.child_count }} child{{ ripple.child_count === 1 ? '' : 'ren' }}
      </span>
      <span class="ripple-card__confidence ripple-confidence" data-testid="ripple-confidence">
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
.ripple-card__status { font-size: var(--text-sm); padding: 4px 10px; border-radius: 4px; }
.ripple-card__status--pending { background: #fff3cd; color: #856404; }
.ripple-card__status--applied { background: #d4edda; color: #155724; }
.ripple-card__status--rejected { background: #f8d7da; color: #721c24; }
.ripple-card__dim { font-weight: 600; font-size: var(--text-md); color: #2c3e50; }
.ripple-card__body { display: flex; gap: 12px; font-size: var(--text-sm); color: #555; }
.ripple-card__footer { margin-top: 8px; font-size: var(--text-sm); color: #666; }
</style>
