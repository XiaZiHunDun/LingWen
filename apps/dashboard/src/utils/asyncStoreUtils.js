import { onBeforeUnmount, onMounted } from 'vue';
import { logger } from './logger.js';

export function createSingletonLifecycle(refreshFn, options = {}) {
  const {
    autoRefresh = true,
    deferRefresh = true,
  } = options;

  let mountedCount = 0;

  function useLifecycle() {
    onMounted(() => {
      if (mountedCount === 0 && autoRefresh) {
        if (deferRefresh) {
          Promise.resolve().then(() => refreshFn());
        } else {
          refreshFn();
        }
      }
      mountedCount += 1;
    });

    onBeforeUnmount(() => {
      mountedCount = Math.max(0, mountedCount - 1);
    });
  }

  return { useLifecycle };
}

export function withLoadingState(refreshFn, loading, lastError, options = {}) {
  const { rethrow = false } = options;
  return async function wrappedRefresh(...args) {
    loading.value = true;
    lastError.value = null;
    try {
      const result = await refreshFn(...args);
      return result;
    } catch (e) {
      lastError.value = e instanceof Error ? e.message : String(e);
      logger.error(`[withLoadingState] Refresh failed:`, e);
      if (rethrow) {
        throw e;
      }
    } finally {
      loading.value = false;
    }
  };
}
