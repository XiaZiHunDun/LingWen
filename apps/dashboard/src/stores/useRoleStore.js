/**
 * Role Store - Manages user role and permissions
 *
 * @typedef {Object} RoleStoreState
 * @property {boolean} isReviewer - 是否为审阅者模式
 * @property {boolean} isReadonlyInsight - 洞察页是否只读
 * @property {Set<string>} blockedNav - 审阅者被屏蔽的导航项 (computed)
 *
 * 注意：Pinia store 属性已自动解包，不需要 .value。直接使用 roleStore.isReviewer 即可。
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useRoleStore = defineStore('role', () => {
  const isReviewer = ref(false)
  const isReadonlyInsight = ref(false)

  function checkUrlRole() {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    isReviewer.value = params.get('role') === 'reviewer' || params.get('review') === '1'
    isReadonlyInsight.value = isReviewer.value
  }

  function setReviewer(value) {
    isReviewer.value = value
    isReadonlyInsight.value = value
  }

  const blockedNav = computed(() => {
    if (!isReviewer.value) return new Set()
    return new Set([
      'write', 'creator', 'produce', 'library', 'more', 'settings', 'cascade-runs',
      'studio', 'chapters', 'workflows',
    ])
  })

  return {
    isReviewer,
    isReadonlyInsight,
    blockedNav,
    checkUrlRole,
    setReviewer,
  }
})