/**
 * Connectivity Store - Manages API connectivity state
 *
 * @typedef {Object} ConnectivityStoreState
 * @property {boolean} offline - 是否离线
 * @property {string} message - 连接状态消息
 * @property {boolean} checking - 是否正在检查连接
 *
 * 注意：Pinia store 属性已自动解包，不需要 .value。直接使用 connectivityStore.offline 即可。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConnectivityStore = defineStore('connectivity', () => {
  const offline = ref(false)
  const message = ref('')
  const checking = ref(false)

  function markOnline() {
    offline.value = false
    message.value = ''
    checking.value = false
  }

  function markOffline(msg) {
    offline.value = true
    message.value = msg
    checking.value = false
  }

  function setChecking(value) {
    checking.value = value
  }

  async function retryCheck() {
    checking.value = true
    try {
      const response = await fetch('/api/health', { timeout: 5000 })
      if (response.ok) {
        markOnline()
        return true
      }
    } catch {
      markOffline('无法连接到服务器，请检查网络连接')
    }
    return false
  }

  return {
    offline,
    message,
    checking,
    markOnline,
    markOffline,
    setChecking,
    retryCheck,
  }
})
