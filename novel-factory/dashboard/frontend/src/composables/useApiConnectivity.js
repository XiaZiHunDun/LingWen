import { onMounted, onUnmounted } from 'vue';
import { apiConnectivity } from '../api/connectivity.js';
import { fetchHealth } from '../api/index.js';

const ONLINE_POLL_MS = 60_000;
const OFFLINE_POLL_MS = 15_000;

/**
 * Global API reachability — health probe + shared state from request() failures.
 */
export function useApiConnectivity() {
  let timer = null;

  async function check() {
    apiConnectivity.value = { ...apiConnectivity.value, checking: true };
    try {
      await fetchHealth();
      apiConnectivity.value = { offline: false, message: '', checking: false };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
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
