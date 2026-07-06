<!--
  SidebarWsDisconnectedBanner.vue — Sidebar 全局 WebSocket 断线 indicator (Phase 9.26 F10)
-->
<template>
  <div
    v-if="isDisconnected"
    class="ws-disconnected-banner"
    data-testid="ws-disconnected-banner"
    role="alert"
    aria-live="assertive"
  >
    实时同步已断开，页面数据可能过期
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';

const { connected } = useWorkflowSocket();
const hasMounted = ref(false);
onMounted(() => {
  setTimeout(() => { hasMounted.value = true; }, 200);
});
const isDisconnected = computed(() => hasMounted.value && !connected.value);
</script>

<style scoped>
.ws-disconnected-banner {
  background: #fff8e8;
  color: #7a4b00;
  border: var(--border-width) solid #e8c468;
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-size: var(--text-xs);
  line-height: 1.45;
  font-family: var(--font-ui);
  font-weight: 500;
}
</style>
