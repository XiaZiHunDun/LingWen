<!-- dashboard/frontend/src/components/RippleDrawer.vue (NEW, Phase 9.13) -->
<template>
  <div v-if="open" class="ripple-drawer ripple-drawer" data-testid="ripple-drawer" @click.self="$emit('close')">
    <div class="ripple-drawer__panel ripple-drawer-content" data-testid="ripple-drawer-content">
      <header class="ripple-drawer__header">
        <h2>{{ ripple.dimension }} — {{ ripple.relationship_type }}</h2>
        <button class="ripple-drawer-close" data-testid="ripple-drawer-close" @click="$emit('close')">×</button>
      </header>
      <section class="ripple-drawer__body">
        <div class="ripple-drawer__row">
          <span class="ripple-drawer__label">Status:</span>
          <span :class="`ripple-drawer__status--${ripple.status} ripple-drawer-status`">{{ ripple.status }}</span>
        </div>
        <div class="ripple-drawer__row">
          <span class="ripple-drawer__label">Source chapter:</span> {{ ripple.source_chapter }}
        </div>
        <div class="ripple-drawer__row">
          <span class="ripple-drawer__label">Target chapter:</span> {{ ripple.target_chapter }}
        </div>
        <div class="ripple-drawer__row">
          <span class="ripple-drawer__label">Confidence:</span> {{ ripple.confidence }}/5
        </div>
        <details class="ripple-drawer__evidence">
          <summary>Evidence</summary>
          <pre>{{ ripple.evidence }}</pre>
        </details>
        <details class="ripple-drawer__payload">
          <summary>Source payload</summary>
          <pre>{{ JSON.stringify(ripple.source_payload, null, 2) }}</pre>
        </details>
        <details class="ripple-drawer__payload">
          <summary>Edge payload</summary>
          <pre>{{ JSON.stringify(ripple.edge_payload, null, 2) }}</pre>
        </details>
        <!-- Phase 9.14: audit timeline section (auditEntries latest 5) -->
        <div class="ripple-audit-timeline ripple-audit-list" v-if="auditEntries.length > 0">
          <h4>Audit History (latest {{ Math.min(5, auditEntries.length) }})</h4>
          <ul class="ripple-audit-list" data-testid="ripple-audit-list">
            <li
              v-for="entry in auditEntries.slice(0, 5)"
              :key="entry.id"
              class="ripple-audit-entry"
              data-testid="ripple-audit-entry"
            >
              <span class="audit-time ripple-audit-entry">{{ entry.created_at }}</span>
              <span class="audit-action ripple-audit-entry">{{ entry.action }}</span>
              <span class="audit-actor ripple-audit-entry">by {{ entry.actor }} ({{ entry.origin }})</span>
              <span v-if="entry.reason" class="audit-reason ripple-audit-entry">"{{ entry.reason }}"</span>
            </li>
          </ul>
        </div>
        <div
          v-else
          class="ripple-audit-empty ripple-audit-list"
          data-testid="ripple-audit-empty"
        >No history yet</div>
      </section>
      <footer class="ripple-drawer__footer">
        <button
          class="ripple-drawer-apply"
          data-testid="ripple-drawer-apply"
          :disabled="isTerminal"
          @click="$emit('apply', ripple)"
        >Apply</button>
        <button
          class="ripple-drawer-reject"
          data-testid="ripple-drawer-reject"
          :disabled="isTerminal"
          @click="$emit('reject', ripple)"
        >Reject</button>
        <button
          v-if="canRollback"
          class="btn btn-warning ripple-rollback-btn"
          data-testid="ripple-rollback-btn"
          @click="onRollbackClick"
        >Rollback</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRippleStore } from '../composables/useRippleStore.js';

const props = defineProps({
  ripple: { type: Object, required: true },
  open: { type: Boolean, default: false },
});
const emit = defineEmits(['close', 'apply', 'reject']);

const isTerminal = computed(() => ['applied', 'rejected', 'failed'].includes(props.ripple.status));

// Phase 9.14: audit timeline + Rollback button (0 改既有 apply/reject logic)
const store = useRippleStore();
const auditEntries = ref([]);

const canRollback = computed(() => {
  if (!props.ripple) return false;
  return props.ripple.status === 'applied' || props.ripple.status === 'rejected';
});

async function loadAudit() {
  if (!props.ripple || !props.ripple.ripple_id) return;
  try {
    auditEntries.value = await store.fetchAudit(props.ripple.ripple_id);
  } catch (e) {
    auditEntries.value = [];
  }
}

async function onRollbackClick() {
  const reason = window.prompt('Reason for rollback? (required)');
  if (!reason || !reason.trim()) return;  // cancel or empty → no-op (防误点)
  await store.rollback(props.ripple.ripple_id, reason);
  emit('close');
}

onMounted(loadAudit);
watch(() => props.ripple && props.ripple.ripple_id, loadAudit);
</script>

<style scoped>
.ripple-drawer {
  position: fixed; top: 0; right: 0; bottom: 0; left: 0;
  background: rgba(0, 0, 0, 0.4); z-index: 1000;
  display: flex; justify-content: flex-end;
}
.ripple-drawer__panel {
  width: 480px; background: #fff; height: 100%; overflow-y: auto;
  display: flex; flex-direction: column;
}
.ripple-drawer__header { display: flex; justify-content: space-between; padding: 16px 24px; border-bottom: 1px solid #eee; }
.ripple-drawer__header h2 { margin: 0; font-size: 1.1em; }
.ripple-drawer__body { padding: 16px 24px; flex: 1; }
.ripple-drawer__row { display: flex; gap: 8px; margin-bottom: 8px; }
.ripple-drawer__label { font-weight: 600; color: #555; min-width: 120px; }
.ripple-drawer__status--pending { color: #856404; }
.ripple-drawer__status--applied { color: #155724; }
.ripple-drawer__status--rejected { color: #721c24; }
.ripple-drawer__evidence, .ripple-drawer__payload { margin-top: 12px; }
.ripple-drawer__evidence pre, .ripple-drawer__payload pre {
  background: #f6f8fa; padding: 8px; border-radius: 4px; font-size: 0.85em; overflow-x: auto;
}
.ripple-drawer__footer { padding: 16px 24px; border-top: 1px solid #eee; display: flex; gap: 12px; }
.ripple-drawer__footer button {
  flex: 1; padding: 8px 16px; border: none; border-radius: 4px;
  background: #2c3e50; color: white; cursor: pointer; font-size: 0.95em;
}
.ripple-drawer__footer button:disabled { background: #999; cursor: not-allowed; }
.ripple-drawer__footer button[data-testid="ripple-drawer-reject"] { background: #c0392b; }
.ripple-drawer__footer button[data-testid="ripple-rollback-btn"] { background: #d97706; }
.ripple-audit-timeline { margin-top: 16px; padding: 12px; background: #fafbfc; border-radius: 4px; }
.ripple-audit-timeline h4 { margin: 0 0 8px 0; font-size: 0.95em; color: #444; }
.ripple-audit-list { list-style: none; padding: 0; margin: 0; }
.ripple-audit-entry { padding: 4px 0; font-size: 0.85em; color: #555; display: block; }
.ripple-audit-empty { margin-top: 12px; padding: 8px; color: #888; font-style: italic; font-size: 0.85em; }
</style>
