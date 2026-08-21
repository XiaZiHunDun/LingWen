/**
 * Studio Store - Manages project and creator state
 *
 * @typedef {Object} StudioStoreState
 * @property {Array} projects - 项目列表
 * @property {string|null} activeSlug - 当前活跃项目 slug
 * @property {Object|null} summary - 项目摘要
 * @property {Object|null} overview - 项目概览
 * @property {boolean} loading - 加载状态
 * @property {Object|null} quality - 质量数据
 * @property {Object|null} qualityReport - 质量报告
 * @property {Object|null} proseDiff - 散文差异
 * @property {Object|null} proseJudge - 散文评判
 * @property {string|null} error - 错误信息
 * @property {number} projectRevision - 项目版本号
 * @property {Object|null} activeProject - 活跃项目 (computed)
 *
 * 注意：Pinia store 属性已自动解包，不需要 .value。直接使用 studioStore.summary 即可。
 */

import { defineStore } from 'pinia'
import { ref, shallowRef, computed } from 'vue'
import {
  fetchStudioProjects,
  fetchStudioSummary,
  setStudioActive,
  fetchCreatorOverview,
  fetchStudioQuality,
  fetchStudioQualityReport,
  fetchStudioProseDiff,
  fetchStudioProseJudge,
} from '../api/index.js'
import { logger } from '../utils/logger.js'

const CACHE_TTL_MS = 30000;

function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

export const useStudioStore = defineStore('studio', () => {
  const projects = shallowRef([]) // Phase 77: shallowRef — wholesale replacement (line 46)
  const activeSlug = ref(null)
  const summary = shallowRef(null) // Phase 77: shallowRef — wholesale replacement (line 48)
  const overview = shallowRef(null) // Phase 77: shallowRef — wholesale replacement (line 49)
  const loading = ref(false)
  const quality = shallowRef(null) // Phase 77: shallowRef — wholesale replacement (line 51)
  const qualityReport = shallowRef(null) // Phase 77: shallowRef — wholesale replacement (line 52)
  const proseDiff = shallowRef(null) // Phase 77: shallowRef — wholesale replacement (line 53)
  const proseJudge = shallowRef(null) // Phase 77: shallowRef — wholesale replacement (line 54)
  const error = ref(null)
  const projectRevision = ref(0)

  const cacheTimestamps = ref({
    projects: 0,
    summary: 0,
    overview: 0,
    quality: 0,
    qualityReport: 0,
    proseDiff: 0,
    proseJudge: 0,
  })

  function isCacheValid(key) {
    return Date.now() - cacheTimestamps.value[key] < CACHE_TTL_MS
  }

  function updateCacheTimestamp(key) {
    cacheTimestamps.value[key] = Date.now()
  }

  const activeProject = computed(() => {
    if (!activeSlug.value) return null
    return projects.value.find((p) => p.slug === activeSlug.value) || {
      slug: activeSlug.value,
      name: summary.value?.name,
    }
  })

  function bumpProjectRevision() {
    projectRevision.value += 1
  }

  async function loadProjects() {
    if (isCacheValid('projects') && projects.value.length > 0) {
      return { projects: projects.value, active_slug: activeSlug.value }
    }
    loading.value = true
    try {
      const data = await fetchStudioProjects()
      projects.value = data.projects || []
      activeSlug.value = data.active_slug || null
      updateCacheTimestamp('projects')
      return data
    } catch (error) {
      logger.error('Failed to load projects:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function switchProject(slug) {
    const data = await setStudioActive(slug)
    activeSlug.value = data.slug
    bumpProjectRevision()
    await refresh(true)
    return data
  }

  async function refresh(force = false) {
    loading.value = true
    error.value = null
    try {
      await loadProjects()
      const fetchTasks = []
      if (force || !isCacheValid('summary')) {
        fetchTasks.push(fetchStudioSummary().then(data => {
          summary.value = data
          updateCacheTimestamp('summary')
        }))
      }
      if (force || !isCacheValid('quality')) {
        fetchTasks.push(fetchStudioQuality().then(data => {
          quality.value = data
          updateCacheTimestamp('quality')
        }))
      }
      if (force || !isCacheValid('qualityReport')) {
        fetchTasks.push(fetchStudioQualityReport().then(data => {
          qualityReport.value = data
          updateCacheTimestamp('qualityReport')
        }))
      }
      if (force || !isCacheValid('proseDiff')) {
        fetchTasks.push(fetchStudioProseDiff().then(data => {
          proseDiff.value = data
          updateCacheTimestamp('proseDiff')
        }))
      }
      if (force || !isCacheValid('proseJudge')) {
        fetchTasks.push(fetchStudioProseJudge().then(data => {
          proseJudge.value = data
          updateCacheTimestamp('proseJudge')
        }))
      }
      await Promise.all(fetchTasks)
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  const debouncedRefresh = debounce(() => refresh(), 500)

  async function loadSummary() {
    if (isCacheValid('summary') && summary.value) {
      return summary.value
    }
    loading.value = true
    try {
      summary.value = await fetchStudioSummary()
      if (summary.value) {
        activeSlug.value = summary.value.slug
      }
      updateCacheTimestamp('summary')
      return summary.value
    } catch (error) {
      logger.error('Failed to load summary:', error)
    } finally {
      loading.value = false
    }
  }

  async function loadOverview() {
    if (isCacheValid('overview') && overview.value) {
      return overview.value
    }
    loading.value = true
    try {
      overview.value = await fetchCreatorOverview()
      updateCacheTimestamp('overview')
      return overview.value
    } catch (error) {
      logger.error('Failed to load overview:', error)
    } finally {
      loading.value = false
    }
  }

  async function setActive(slug) {
    loading.value = true
    try {
      await setStudioActive(slug)
      activeSlug.value = slug
      Object.keys(cacheTimestamps.value).forEach(key => {
        cacheTimestamps.value[key] = 0
      })
    } catch (error) {
      logger.error('Failed to set active project:', error)
    } finally {
      loading.value = false
    }
  }

  async function init() {
    await loadSummary()
    await loadProjects()
    await loadOverview()
  }

  return {
    projects,
    activeSlug,
    summary,
    overview,
    loading,
    quality,
    qualityReport,
    proseDiff,
    proseJudge,
    error,
    projectRevision,
    activeProject,
    loadProjects,
    loadSummary,
    loadOverview,
    setActive,
    init,
    switchProject,
    debouncedRefresh,
    refresh,
    bumpProjectRevision,
  }
})
