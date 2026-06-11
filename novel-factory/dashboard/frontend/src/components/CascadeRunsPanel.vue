<!-- dashboard/frontend/src/components/CascadeRunsPanel.vue (NEW, Phase 9.22 T2) -->
<!-- Per-ripple Cascade runs tab: 表格 (ID/Status/Depth/Created/Actions) + Replay +
  Cancel buttons + WS handler via Phase 9.17 useWorkflowSocket.onCascadeUpdate.
  Replay 调新 fetchCascadeWithDepth 走 Phase 9.20 ?persist=false read-only path,
  0 污染 cascade_runs 表. Cancel 走 Phase 9.21 既 endpoint (idempotent). -->
<template>
  <div class="cascade-runs-panel" data-testid="cascade-runs-panel">
    <CascadeRunsFilter
      :model-value="filters"
      @update:model-value="onFilterChange"
    />
    <div v-if="loading" class="cascade-runs-loading" data-testid="cascade-runs-loading">
      Loading cascade runs...
    </div>
    <div v-else-if="error" class="cascade-runs-error" data-testid="cascade-runs-error">
      {{ error }}
    </div>
    <div v-else-if="runs.length === 0" class="cascade-runs-empty" data-testid="cascade-runs-empty">
      {{ hasActiveFilter ? 'No cascade runs match these filters' : 'No cascade runs yet' }}
    </div>
    <table v-else class="cascade-runs-table" data-testid="cascade-runs-table">
      <thead>
        <tr>
          <th>ID</th><th>Status</th><th>Depth</th><th>Created</th><th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="run in runs"
          :key="run.id"
          class="cascade-run-row"
          :class="{ 'is-selected': selectedRunId === run.id }"
          :data-run-id="run.id"
          :data-status="run.status"
          data-testid="cascade-run-row"
        >
          <td>{{ run.id }}</td>
          <td>
            <span
              :class="`status-badge status-${run.status}`"
              :data-testid="`status-badge-${run.status}`"
            >{{ run.status }}</span>
          </td>
          <td>{{ run.max_depth }}</td>
          <td :title="run.started_at">{{ formatRelative(run.started_at) }}</td>
          <td>
            <button
              class="replay-btn"
              :disabled="replaying === run.id"
              data-testid="replay-btn"
              @click="replay(run)"
            >Replay</button>
            <button
              v-if="run.status === 'running'"
              class="cancel-btn"
              :disabled="cancelling === run.id"
              data-testid="cancel-btn"
              @click="cancel(run)"
            >Cancel</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="replayedData" class="cascade-runs-replay" data-testid="cascade-runs-replay">
      <p class="cascade-runs-replay-note replay-note" data-testid="replay-note">
        Replayed from run #{{ replayedFromId }} ({{ formatRelative(replayedFromStartedAt) }})
      </p>
      <div class="replay-graph" data-testid="replay-graph">
        <CascadeGraph :cascade="replayedData" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  fetchCascadeRuns,
  cancelCascadeRun,
  fetchCascadeWithDepth,
} from '../api/index.js';
import { onCascadeUpdate } from '../composables/useWorkflowSocket.js';
import CascadeGraph from './CascadeGraph.vue';
import CascadeRunsFilter from './CascadeRunsFilter.vue';

const props = defineProps({
  rippleId: { type: String, required: true },
});

// Phase 9.23 T5: URL search params ↔ filter state sync.
// queryToFilters: snake_case URL → camelCase JS (string numbers parsed).
// filtersToQuery: camelCase JS → snake_case URL (nulls + 'all' omitted).
const route = useRoute();
const router = useRouter();

const DEFAULT_FILTERS = Object.freeze({
  status: 'all', minDepth: null, maxDepth: null, algorithm: 'all',
});

function queryToFilters(query) {
  const minD = query.min_depth ? Number(query.min_depth) : null;
  const maxD = query.max_depth ? Number(query.max_depth) : null;
  return {
    status: query.status || 'all',
    minDepth: minD != null && Number.isFinite(minD) ? minD : null,
    maxDepth: maxD != null && Number.isFinite(maxD) ? maxD : null,
    algorithm: query.algorithm || 'all',
  };
}

function filtersToQuery(filters) {
  const q = {};
  if (filters.status && filters.status !== 'all') q.status = filters.status;
  if (filters.minDepth != null && filters.minDepth !== '') q.min_depth = String(filters.minDepth);
  if (filters.maxDepth != null && filters.maxDepth !== '') q.max_depth = String(filters.maxDepth);
  if (filters.algorithm && filters.algorithm !== 'all') q.algorithm = filters.algorithm;
  return q;
}

const filters = ref(queryToFilters(route.query));

const hasActiveFilter = computed(() =>
  filters.value.status !== 'all' ||
  filters.value.minDepth != null ||
  filters.value.maxDepth != null ||
  filters.value.algorithm !== 'all'
);

const runs = ref([]);
const loading = ref(false);
const error = ref(null);
const replaying = ref(null);
const cancelling = ref(null);
const replayedData = ref(null);
const replayedFromId = ref(null);
const replayedFromStartedAt = ref(null);
const selectedRunId = ref(null);

async function loadRuns() {
  loading.value = true;
  error.value = null;
  try {
    const opts = {};
    if (filters.value.status !== 'all') opts.status = filters.value.status;
    if (filters.value.minDepth != null) opts.minDepth = filters.value.minDepth;
    if (filters.value.maxDepth != null) opts.maxDepth = filters.value.maxDepth;
    if (filters.value.algorithm !== 'all') opts.algorithm = filters.value.algorithm;
    runs.value = await fetchCascadeRuns(props.rippleId, opts);
  } catch (e) {
    error.value = `Failed to load cascade runs: ${e?.message || e}`;
    runs.value = [];
  } finally {
    loading.value = false;
  }
}

// Phase 9.23 T5: filter → URL + refetch (CascadeRunsFilter emit handler).
function onFilterChange(next) {
  filters.value = next;
  router.replace({ query: filtersToQuery(next) });
  loadRuns();
}

// Phase 9.23 T5: URL → state (handles back/forward + deep links).
// JSON.stringify diff avoids dead loop when we just wrote the query ourselves.
watch(() => route.query, (q) => {
  const next = queryToFilters(q);
  if (JSON.stringify(next) !== JSON.stringify(filters.value)) {
    filters.value = next;
    loadRuns();
  }
});

function formatRelative(iso) {
  if (!iso) return '';
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffSec = Math.max(0, Math.round((now - then) / 1000));
  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffSec < 3600) return `${Math.round(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.round(diffSec / 3600)}h ago`;
  return `${Math.round(diffSec / 86400)}d ago`;
}

async function replay(run) {
  if (replaying.value) return;
  replaying.value = run.id;
  try {
    const data = await fetchCascadeWithDepth(props.rippleId, run.max_depth);
    replayedData.value = data;
    replayedFromId.value = run.id;
    replayedFromStartedAt.value = run.started_at;
    selectedRunId.value = run.id;
  } catch (e) {
    error.value = `Replay failed: ${e?.message || e}`;
  } finally {
    replaying.value = null;
  }
}

async function cancel(run) {
  if (cancelling.value) return;
  cancelling.value = run.id;
  const prevStatus = run.status;
  // Optimistic update
  run.status = 'cancelled';
  try {
    await cancelCascadeRun(props.rippleId, run.id, '');
    // WS cascade.cancel event will arrive shortly and re-confirm (idempotent)
  } catch (e) {
    // Revert on failure
    run.status = prevStatus;
    error.value = `Cancel failed: ${e?.message || e}`;
  } finally {
    cancelling.value = null;
  }
}

// Phase 9.17 WS cascade handler: cascade.update → re-fetch; cascade.cancel → status
// 接受 2 种 event shape:
//   1) production (unwrapped): { ripple_id, run_id?, status?, reason? }
//   2) test-injected (envelope): { type: 'cascade.cancel', payload: { ... } }
let unsubscribeCascade = null;
onMounted(async () => {
  await loadRuns();
  unsubscribeCascade = onCascadeUpdate((event) => {
    const data = event?.payload && typeof event.payload === 'object' ? event.payload : event;
    if (!data || data.ripple_id !== props.rippleId) return;
    if (data.status === 'cancelled' && data.run_id != null) {
      // Phase 9.21 cascade.cancel event: update specific row
      const existing = runs.value.find((r) => r.id === data.run_id);
      if (existing) existing.status = 'cancelled';
    } else {
      // Phase 9.17 cascade.update event: payload lacks run_id, re-fetch entire list
      loadRuns();
    }
  });
});

onBeforeUnmount(() => {
  if (typeof unsubscribeCascade === 'function') {
    unsubscribeCascade();
  }
});
</script>

<style scoped>
.cascade-runs-panel { margin-top: 12px; }
.cascade-runs-loading, .cascade-runs-error, .cascade-runs-empty {
  padding: 16px; text-align: center; color: #555; font-size: 0.9em;
}
.cascade-runs-error { color: #c0392b; }
.cascade-runs-table {
  width: 100%; border-collapse: collapse; font-size: 0.85em;
  max-height: 400px; overflow-y: auto; display: block;
}
.cascade-runs-table thead, .cascade-runs-table tbody { display: table; width: 100%; table-layout: fixed; }
.cascade-runs-table th, .cascade-runs-table td {
  text-align: left; padding: 8px 12px; border-bottom: 1px solid #eee;
}
.cascade-runs-table th { background: #fafbfc; font-weight: 600; color: #444; }
.cascade-runs-table tr.is-selected { background: #f0f9ff; }
.cascade-runs-table tr:hover { background: #f6f8fa; }
.status-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;
}
.status-running { background: #dbeafe; color: #1e40af; animation: cascade-runs-pulse 1.5s infinite; }
.status-completed { background: #dcfce7; color: #14532d; }
.status-cancelled { background: #f3f4f6; color: #6b7280; text-decoration: line-through; }
.status-failed { background: #fee2e2; color: #991b1b; }
@keyframes cascade-runs-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.replay-btn, .cancel-btn {
  padding: 4px 12px; border: 1px solid #2c3e50; background: #fff; color: #2c3e50;
  border-radius: 4px; cursor: pointer; font-size: 0.85em; margin-right: 4px;
}
.replay-btn:hover:not(:disabled), .cancel-btn:hover:not(:disabled) {
  background: #2c3e50; color: #fff;
}
.replay-btn:disabled, .cancel-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cancel-btn { border-color: #c0392b; color: #c0392b; }
.cancel-btn:hover:not(:disabled) { background: #c0392b; color: #fff; }
.cascade-runs-replay { margin-top: 16px; padding: 12px; background: #fafbfc; border-radius: 4px; }
.cascade-runs-replay-note { margin: 0 0 8px 0; font-size: 0.85em; color: #555; font-style: italic; }
</style>
