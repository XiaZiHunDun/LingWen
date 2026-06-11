<!--
  SidebarWsDisconnectedBanner.vue — Sidebar 全局 WebSocket 断线 indicator (Phase 9.26 F10)
  从 SidebarCostBanner (Phase 8.27) 提升到 App sidebar 层级, 不依赖 hasCost gate.
  hasMounted 200ms gate 避免初次 mount flash; 真断线 → 黄色 pulse animation.
-->
<template>
  <div
    v-if="isDisconnected"
    class="ws-disconnected-banner"
    data-testid="ws-disconnected-banner"
    role="alert"
    aria-live="assertive"
  >
    ⚠️ 实时同步已断开, 页面数据可能过期
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
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffc107;
  border-radius: 2px;
  padding: 4px 6px;
  font-size: 7px;
  line-height: 1.4;
  text-align: center;
  font-family: 'Press Start 2P', monospace;
  animation: ws-disconnected-pulse 1.5s ease-in-out infinite;
}

@keyframes ws-disconnected-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
