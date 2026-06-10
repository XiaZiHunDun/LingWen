<!-- dashboard/frontend/src/pages/RipplesPage.vue (NEW, Phase 9.13) -->
<template>
  <div class="ripples-page">
    <h1>Ripples</h1>
    <RippleFilter
      v-model:status="filter.status"
      v-model:dimension="filter.dimension"
      v-model:volume="filter.volume"
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
import { useRippleStore } from '../composables/useRippleStore.js';
import { useRippleSocket } from '../composables/useRippleSocket.js';
import { fetchRippleDetail } from '../api/index.js';

const store = useRippleStore();
const socket = useRippleSocket();

const filter = ref({ status: 'all', dimension: 'all', volume: 'all' });
const selectedRipple = ref(null);
const drawerOpen = ref(false);

onMounted(() => {
  store.refresh(filterToFilters(filter.value));
  socket.connect();
});

watch(filter, (f) => {
  store.refresh(filterToFilters(f));
}, { deep: true });

watch(() => socket.pendingUpdates.value, (updates) => {
  updates.forEach((u) => store.applySocketUpdate(u));
  socket.pendingUpdates.value = [];
});

function filterToFilters(f) {
  const out = {};
  if (f.status !== 'all') out.status = f.status;
  if (f.volume !== 'all') out.volume = Number(f.volume);
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
}

async function rejectSelected() {
  if (!selectedRipple.value) return;
  await store.reject(selectedRipple.value.ripple_id);
  drawerOpen.value = false;
}
</script>

<style scoped>
.ripples-page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.ripples-page h1 { margin-bottom: 16px; }
</style>
