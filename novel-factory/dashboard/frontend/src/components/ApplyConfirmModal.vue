<!-- dashboard/frontend/src/components/ApplyConfirmModal.vue (NEW, Phase 9.15 T4) -->
<!-- Generic 2-button confirmation modal (used by RippleDrawer before apply).
  0 store mutation on cancel; confirm emits event; parent decides action.
  Scope: dry-run flow only (cascade BFS preview → confirm). Reusable
  in future apply-style flows (e.g., reject confirm). 0 改既有 modal style. -->
<template>
  <div
    v-if="isOpen"
    class="apply-confirm-modal"
    data-testid="apply-confirm-modal"
    @click.self="$emit('cancel')"
  >
    <div class="apply-confirm-modal__panel" data-testid="apply-confirm-modal-panel">
      <h3>Confirm Apply</h3>
      <div class="apply-confirm-modal__chips" data-testid="apply-confirm-chips">
        <span class="chip apply-confirm-chip" data-testid="apply-confirm-chapter-count">
          {{ totals.affected_chapter_count || 0 }} chapter(s)
        </span>
        <span class="chip apply-confirm-chip" data-testid="apply-confirm-character-count">
          {{ totals.affected_character_count || 0 }} character(s)
        </span>
        <span class="chip apply-confirm-chip" data-testid="apply-confirm-setting-count">
          {{ totals.affected_setting_count || 0 }} setting(s)
        </span>
        <span class="chip apply-confirm-chip" data-testid="apply-confirm-change-count">
          {{ totals.estimated_change_count || 0 }} change(s)
        </span>
      </div>
      <p class="apply-confirm-modal__warning">
        This will apply cascade changes. Use Rollback to reverse.
      </p>
      <div class="apply-confirm-modal__buttons">
        <button
          type="button"
          class="apply-confirm-cancel"
          data-testid="apply-confirm-cancel"
          @click="$emit('cancel')"
        >Cancel</button>
        <button
          type="button"
          class="apply-confirm-apply"
          data-testid="apply-confirm-apply"
          @click="$emit('confirm')"
        >Apply</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isOpen: { type: Boolean, default: false },
  totals: {
    type: Object,
    default: () => ({
      affected_chapter_count: 0,
      affected_character_count: 0,
      affected_setting_count: 0,
      estimated_change_count: 0,
    }),
  },
})
defineEmits(['confirm', 'cancel'])
</script>

<style scoped>
.apply-confirm-modal {
  position: fixed; top: 0; right: 0; bottom: 0; left: 0;
  background: rgba(0, 0, 0, 0.5); z-index: 1100;
  display: flex; justify-content: center; align-items: center;
}
.apply-confirm-modal__panel {
  background: #fff; padding: 24px; border-radius: 8px;
  max-width: 420px; width: 90%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
.apply-confirm-modal__panel h3 {
  margin: 0 0 16px 0; font-size: 1.15em; color: #222;
}
.apply-confirm-modal__chips {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;
}
.apply-confirm-chip {
  background: #f1f3f5; color: #333;
  padding: 6px 12px; border-radius: 16px;
  font-size: 0.85em;
}
.apply-confirm-modal__warning {
  color: #c0392b; font-size: 0.85em; margin: 0 0 20px 0;
}
.apply-confirm-modal__buttons {
  display: flex; gap: 12px;
}
.apply-confirm-modal__buttons button {
  flex: 1; padding: 10px 16px; border: none; border-radius: 4px;
  cursor: pointer; font-size: 0.95em;
}
.apply-confirm-cancel {
  background: #e9ecef; color: #333;
}
.apply-confirm-cancel:hover { background: #dee2e6; }
.apply-confirm-apply {
  background: #c0392b; color: white;
}
.apply-confirm-apply:hover { background: #a93226; }
</style>
