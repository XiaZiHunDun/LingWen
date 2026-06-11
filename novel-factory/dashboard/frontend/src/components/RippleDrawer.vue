<!-- dashboard/frontend/src/components/RippleDrawer.vue (Phase 9.13 + 9.22 T3) -->
<!-- Per-ripple drawer: 3 tabs (Summary / Cascade / Runs) wrapping existing body content. -->
<template>
  <div v-if="open" class="ripple-drawer ripple-drawer" data-testid="ripple-drawer" @click.self="$emit('close')">
    <div class="ripple-drawer__panel ripple-drawer-content" data-testid="ripple-drawer-content">
      <header class="ripple-drawer__header">
        <h2>{{ ripple.dimension }} — {{ ripple.relationship_type }}</h2>
        <button class="ripple-drawer-close" data-testid="ripple-drawer-close" @click="$emit('close')">×</button>
      </header>
      <nav class="ripple-drawer__tabs" data-testid="ripple-drawer-tabs">
        <button :class="['tab', { active: activeTab === 'summary' }]"
                data-testid="tab-summary"
                @click="activeTab = 'summary'">Summary</button>
        <button :class="['tab', { active: activeTab === 'cascade' }]"
                data-testid="tab-cascade"
                @click="activeTab = 'cascade'">Cascade</button>
        <button :class="['tab', { active: activeTab === 'runs' }]"
                data-testid="tab-cascade-runs"
                @click="activeTab = 'runs'">Cascade runs</button>
      </nav>
      <section class="ripple-drawer__body">
        <!-- Summary tab (existing status rows + evidence + payload, Phase 9.13/9.14) -->
        <div v-if="activeTab === 'summary'" class="drawer-section" data-testid="drawer-summary-section">
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
          <!-- Phase 9.50 F39: 6-state lifecycle timeline -->
          <RippleLifecycleTimeline
            :status="ripple.status"
            :audit-entries="auditEntries"
          />
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
        </div>

        <!-- Cascade tab (existing dry-run preview, Phase 9.15) -->
        <div v-else-if="activeTab === 'cascade'" class="drawer-section" data-testid="drawer-cascade-section">
          <section class="dryrun-section" data-testid="ripple-dryrun-section">
            <header class="dryrun-header">
              <h4>Dry-run preview</h4>
              <button
                type="button"
                class="dryrun-toggle"
                :aria-pressed="showDryRun"
                data-testid="dry-run-toggle"
                @click="onToggleDryRun"
              >{{ showDryRun ? 'Hide' : 'Show' }} cascade</button>
            </header>
            <div v-if="showDryRun && preview" class="dryrun-content">
              <div class="summary-chips" data-testid="ripple-summary-chips">
                <span class="chip" data-testid="dry-run-tag">Depth: {{ preview.max_depth }}</span>
                <span class="chip" data-testid="dry-run-affected-chapters">
                  {{ preview.affected_chapter_count }} chapter(s)
                </span>
                <span class="chip" data-testid="dry-run-affected-characters">
                  {{ preview.affected_character_count }} character(s)
                </span>
                <span class="chip" data-testid="dry-run-affected-settings">
                  {{ preview.affected_setting_count }} setting(s)
                </span>
              </div>
              <CascadeGraph
                v-if="cascade"
                :cascade="cascade"
                :dry-run="true"
                data-testid="cascade-graph"
              />
            </div>
          </section>
        </div>

        <!-- Cascade runs tab (Phase 9.22: historical cascade_runs list + Replay + Cancel) -->
        <div v-else-if="activeTab === 'runs'" class="drawer-section" data-testid="cascade-runs-section">
          <CascadeRunsPanel :ripple-id="ripple.ripple_id" />
        </div>
      </section>
      <footer class="ripple-drawer__footer">
        <button
          class="ripple-drawer-apply"
          data-testid="ripple-drawer-apply"
          :disabled="isTerminal"
          @click="onApplyClick"
        >Apply changes</button>
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
    <!-- Phase 9.15 T4: apply confirmation modal (cancel = no-op, confirm = real apply) -->
    <ApplyConfirmModal
      :is-open="showApplyModal"
      :totals="preview || {}"
      @confirm="onConfirmApply"
      @cancel="showApplyModal = false"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRippleStore } from '../composables/useRippleStore.js';
import { onCascadeUpdate } from '../composables/useWorkflowSocket.js';  // Phase 9.16
import CascadeGraph from './CascadeGraph.vue';
import ApplyConfirmModal from './ApplyConfirmModal.vue';
import CascadeRunsPanel from './CascadeRunsPanel.vue';  // Phase 9.22 T3
import RippleLifecycleTimeline from './RippleLifecycleTimeline.vue';  // Phase 9.50 F39

const props = defineProps({
  ripple: { type: Object, required: true },
  open: { type: Boolean, default: false },
});
const emit = defineEmits(['close', 'apply', 'reject']);

const isTerminal = computed(() => ['applied', 'rejected', 'failed'].includes(props.ripple.status));
const activeTab = ref('summary');  // Phase 9.22 T3: tab state (Summary / Cascade / Runs)

// Phase 9.14: audit timeline + Rollback button (0 改既有 apply/reject logic)
const store = useRippleStore();
const auditEntries = ref([]);

const canRollback = computed(() =>
  props.ripple.status === 'applied' || props.ripple.status === 'rejected'
);

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

// === Phase 9.15 T4: dry-run cascade BFS preview + apply confirmation modal ===

const showDryRun = ref(false);
const showApplyModal = ref(false);
const cascade = ref(null);
const preview = ref(null);

// Phase 9.35: debounced cascade refresh — coalesce rapid WS events + update local refs
const CASCADE_REFRESH_DEBOUNCE_MS = 300;
let cascadeRefreshTimer = null;

function scheduleCascadeRefresh() {
  if (cascadeRefreshTimer) clearTimeout(cascadeRefreshTimer);
  cascadeRefreshTimer = setTimeout(() => {
    cascadeRefreshTimer = null;
    loadCascadeAndPreview();
  }, CASCADE_REFRESH_DEBOUNCE_MS);
}

async function loadCascadeAndPreview() {
  if (!props.ripple || !props.ripple.ripple_id) return;
  try {
    const [c, p] = await Promise.all([
      store.loadCascade(props.ripple.ripple_id),
      store.loadCascadePreview(props.ripple.ripple_id),
    ]);
    cascade.value = c;
    preview.value = p;
  } catch (e) {
    cascade.value = null;
    preview.value = null;
  }
}

function onToggleDryRun() {
  showDryRun.value = !showDryRun.value;
  if (showDryRun.value) {
    loadCascadeAndPreview();
  }
}

async function onApplyClick() {
  // Pre-load preview (idempotent) so modal has totals
  await loadCascadeAndPreview();
  showApplyModal.value = true;
}

function onConfirmApply() {
  showApplyModal.value = false;
  emit('apply', props.ripple);
}

onMounted(() => {
  loadAudit();
  // Eager-load cascade on mount (for "Show cascade" toggle, no flash of empty)
  loadCascadeAndPreview();
  // Phase 9.16/9.35: 匹配当前 ripple → debounced 静默 re-fetch (更新 cascade/preview refs)
  onCascadeUpdate((payload) => {
    if (payload && payload.ripple_id === props.ripple.ripple_id) {
      scheduleCascadeRefresh();
    }
    // 不匹配 ignore (next open 走 9.15 GET 返 fresh data)
  });
});
onBeforeUnmount(() => {
  if (cascadeRefreshTimer) clearTimeout(cascadeRefreshTimer);
});
watch(() => props.ripple && props.ripple.ripple_id, () => {
  loadAudit();
  loadCascadeAndPreview();
});
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
.dryrun-section { margin-top: 16px; padding: 12px; background: #fafbfc; border-radius: 4px; }
.dryrun-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.dryrun-header h4 { margin: 0; font-size: 0.95em; color: #444; }
.dryrun-toggle { padding: 4px 12px; border: 1px solid #2c3e50; background: #fff; color: #2c3e50; border-radius: 4px; cursor: pointer; font-size: 0.85em; }
.dryrun-toggle:hover { background: #2c3e50; color: #fff; }
.dryrun-content { margin-top: 8px; }
.summary-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.chip { background: #e8f4f8; color: #155724; padding: 4px 10px; border-radius: 12px; font-size: 0.8em; }
.ripple-drawer__tabs {
  display: flex; gap: 0; border-bottom: 1px solid #eee;
  padding: 0 24px; background: #fafbfc;
}
.ripple-drawer__tabs .tab {
  padding: 10px 16px; border: none; background: transparent; cursor: pointer;
  font-size: 0.9em; color: #555; border-bottom: 2px solid transparent;
}
.ripple-drawer__tabs .tab:hover { color: #2c3e50; }
.ripple-drawer__tabs .tab.active {
  color: #2c3e50; border-bottom-color: #2c3e50; font-weight: 500;
}
.drawer-section { padding: 0; }
</style>
