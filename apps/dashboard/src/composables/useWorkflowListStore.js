/**
 * 获取 workflows 列表。
 *
 * @returns {{ workflows: Array, loading: boolean, lastError: string|null, refresh: Function }}
 * 注意：返回的属性是 ref 在 reactive context 中已自动解包，不需要 .value。
 */

import { ref } from 'vue'
import { fetchWorkflows } from '../api/index.js'
import { createSingletonLifecycle, withLoadingState } from '../utils/asyncStoreUtils.js'

const workflows = ref([])
const loading = ref(false)
const lastError = ref(null)

async function refreshFn() {
  workflows.value = await fetchWorkflows()
}

const refresh = withLoadingState(refreshFn, loading, lastError)
const { useLifecycle } = createSingletonLifecycle(refresh, { autoRefresh: true, deferRefresh: true })

export function useWorkflowListStore() {
  useLifecycle()
  return { workflows, loading, lastError, refresh }
}
