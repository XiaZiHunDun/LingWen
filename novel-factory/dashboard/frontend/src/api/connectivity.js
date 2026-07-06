import { ref } from 'vue';

/** @type {import('vue').Ref<{ offline: boolean, message: string, checking: boolean }>} */
export const apiConnectivity = ref({
  offline: false,
  message: '',
  checking: false,
});

export function markApiOnline() {
  if (apiConnectivity.value.offline) {
    apiConnectivity.value = { offline: false, message: '', checking: false };
  }
}

export function markApiOffline(message) {
  apiConnectivity.value = { offline: true, message, checking: false };
}
