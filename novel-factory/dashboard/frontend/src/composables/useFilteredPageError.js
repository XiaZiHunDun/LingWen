import { computed, unref } from 'vue';
import { apiConnectivity } from '../api/connectivity.js';
import { filterPageErrorMessage } from '../utils/networkErrorUtils.js';

/**
 * Suppress duplicate network error banners when App shows ApiOfflineBanner.
 * @param {import('vue').MaybeRefOrGetter<unknown>} errorSource
 */
export function useFilteredPageError(errorSource) {
  return computed(() => {
    const raw = typeof errorSource === 'function' ? errorSource() : unref(errorSource);
    return filterPageErrorMessage(raw, apiConnectivity.value.offline);
  });
}
