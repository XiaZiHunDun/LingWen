import { onMounted, onUnmounted } from 'vue';
import { apiConnectivity } from '../api/connectivity.js';
import { useConnectivityStore } from '../stores/useConnectivityStore.js';

const ONLINE_POLL_MS = 60_000;
const OFFLINE_POLL_MS = 15_000;

export function useApiConnectivity() {
  const store = useConnectivityStore();
  let timer = null;

  async function check() {
    store.setChecking(true);
    apiConnectivity.value = { ...apiConnectivity.value, checking: true };
    try {
      await fetch('/api/health', { timeout: 5000 });
      store.markOnline();
      apiConnectivity.value = { offline: false, message: '', checking: false };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      store.markOffline(message);
      apiConnectivity.value = { offline: true, message, checking: false };
    }
  }

  function schedulePoll() {
    if (timer) clearInterval(timer);
    const interval = apiConnectivity.value.offline ? OFFLINE_POLL_MS : ONLINE_POLL_MS;
    timer = setInterval(check, interval);
  }

  onMounted(async () => {
    await check();
    schedulePoll();
  });

  onUnmounted(() => {
    if (timer) clearInterval(timer);
    timer = null;
  });

  return { apiConnectivity, retryCheck: check };
}