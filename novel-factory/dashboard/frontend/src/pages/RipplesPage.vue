<!-- dashboard/frontend/src/pages/RipplesPage.vue — Phase 9.13 + 9.41 F30 ImpactGraph -->
<template>
  <div class="ripples-page" data-testid="ripples-page">
    <h1>Ripples</h1>
    <ImpactGraph
      :graph="referenceGraph"
      data-testid="ripples-page-impact-graph"
      @node-click="onImpactNodeClick"
    />
    <RippleFilter
      v-model:status="filter.status"
      v-model:dimension="filter.dimension"
      v-model:volume="filter.volume"
      v-model:sort-by="filter.sortBy"
      v-model:min-score="filter.minScore"
    />
    <RippleList
      :ripples="store.ripples.value"
      :loading="store.loading.value"
      @select="openDrawer"
    />
    <RippleDrawer
      :ripple="selectedRipple"
      :open="drawerOpen"
      @close="drawerOpen = false"
      @apply="applySelected"
      @reject="rejectSelected"
    />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import RippleFilter from '../components/RippleFilter.vue';
import RippleList from '../components/RippleList.vue';
import RippleDrawer from '../components/RippleDrawer.vue';
import ImpactGraph from '../components/ImpactGraph.vue';
import { useRippleStore } from '../composables/useRippleStore.js';
import { useRippleSocket } from '../composables/useRippleSocket.js';
import { fetchRippleDetail, fetchReferenceGraph } from '../api/index.js';

const store = useRippleStore();
const socket = useRippleSocket();

const filter = ref({ status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' });
const selectedRipple = ref(null);
const drawerOpen = ref(false);
const referenceGraph = ref(null);

async function loadReferenceGraph() {
  const opts = {};
  if (filter.value.volume !== 'all') {
    opts.volume = Number(filter.value.volume);
  }
  if (filter.value.dimension !== 'all') {
    opts.dimension = filter.value.dimension;
  }
  try {
    referenceGraph.value = await fetchReferenceGraph(opts);
  } catch {
    referenceGraph.value = { nodes: [], edges: [], total_node_count: 0, total_edge_count: 0, truncated: false };
  }
}

onMounted(() => {
  store.refresh(filterToFilters(filter.value));
  loadReferenceGraph();
  socket.connect();
});

watch(filter, (f) => {
  store.refresh(filterToFilters(f));
  loadReferenceGraph();
}, { deep: true });

watch(() => socket.pendingUpdates.value, (updates) => {
  updates.forEach((u) => store.applySocketUpdate(u));
  socket.pendingUpdates.value = [];
});

function filterToFilters(f) {
  const out = {};
  if (f.status !== 'all') out.status = f.status;
  if (f.volume !== 'all') out.volume = Number(f.volume);
  if (f.sortBy && f.sortBy !== 'created_at') out.sort_by = f.sortBy;
  if (f.minScore !== '' && f.minScore != null) {
    const n = Number(f.minScore);
    if (!Number.isNaN(n)) out.min_score = n;
  }
  return out;
}

async function openDrawer(ripple) {
  selectedRipple.value = await fetchRippleDetail(ripple.ripple_id);
  drawerOpen.value = true;
}

async function applySelected() {
  if (!selectedRipple.value) return;
  await store.apply(selectedRipple.value.ripple_id);
  drawerOpen.value = false;
  await loadReferenceGraph();
}

async function rejectSelected() {
  if (!selectedRipple.value) return;
  await store.reject(selectedRipple.value.ripple_id);
  drawerOpen.value = false;
}

function onImpactNodeClick(payload) {
  // Phase 9.41: hook for future chapter jump; keep no-op for now (0 router dependency)
  void payload;
}
</script>

<style scoped>
.ripples-page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.ripples-page h1 { margin-bottom: 16px; }
</style>
