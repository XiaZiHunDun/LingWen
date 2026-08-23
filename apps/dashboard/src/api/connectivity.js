/**
 * Connectivity API
 * (3 funcs)
 */

import { ref } from 'vue';

export const apiConnectivity = ref({
  offline: false,
  message: '',
  checking: false,
});

let connectivityStore = null;

export function setConnectivityStore(store) {
  connectivityStore = store;
}

export function markApiOnline() {
  apiConnectivity.value = { offline: false, message: '', checking: false };
  if (connectivityStore) {
    connectivityStore.markOnline();
  }
}

export function markApiOffline(message) {
  apiConnectivity.value = { offline: true, message, checking: false };
  if (connectivityStore) {
    connectivityStore.markOffline(message);
  }
}
