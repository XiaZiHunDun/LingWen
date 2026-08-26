/**
 * Write Workspace Store - Author/Editor dual-mode long-form editor state
 *
 * @typedef {'idle'|'saving'|'saved'|'error'|'conflict'} SaveStatus
 * @typedef {Object} SaveState
 * @property {SaveStatus} status - 自动保存状态机
 * @property {string|null} lastSavedAt - ISO 8601 timestamp of last save
 * @property {boolean} dirty - 是否有未保存改动
 *
 * @typedef {Object} WriteGoal
 * @property {number} daily - 每日字数目标
 * @property {number} todayWritten - 今日已写
 *
 * @typedef {Object} WriteWorkspaceStoreState
 * @property {number|null} chapterId - 当前章节 ID
 * @property {'author'|'editor'} mode - 作者模式 / 编辑模式
 * @property {Array} outline - 章节大纲（含场景元信息）
 * @property {Array} scenes - 场景数组（含 body + wordCount）
 * @property {Array} annotations - Editor 模式行内 P0/P1 标注
 * @property {boolean} aiDrawerOpen - AI 抽屉是否打开
 * @property {WriteGoal} writeGoal - 字数目标
 * @property {SaveState} saveState - 保存状态
 * @property {number} totalWords - 当前场景总字数 (computed)
 *
 * 注意：Pinia store 属性已自动解包，不需要 .value。直接使用 store.mode 即可。
 */

import { defineStore } from 'pinia'
import { shallowRef, computed } from 'vue'
import { splitBodyIntoScenes, joinScenesToBody } from '@/utils/writeWorkspace/sceneParser.js'
import { countBodyWords } from '@/utils/writeWorkspace/wordCounter.js'

export const useWriteWorkspaceStore = defineStore('writeWorkspace', () => {
  const chapterId = shallowRef(null)
  /** @type {'author'|'editor'} */
  const mode = shallowRef('author')
  const outline = shallowRef([])
  const scenes = shallowRef([])
  const annotations = shallowRef([])
  const aiDrawerOpen = shallowRef(false)
  const writeGoal = shallowRef({ daily: 0, todayWritten: 0 })
  const saveState = shallowRef({ status: 'idle', lastSavedAt: null, dirty: false })

  function toggleMode() {
    mode.value = mode.value === 'author' ? 'editor' : 'author'
  }

  function load({ chapterId: cid, frontmatter, body }) {
    chapterId.value = cid
    const parsed = splitBodyIntoScenes(body).map(s => ({ ...s, wordCount: countBodyWords(s.body) }))
    scenes.value = parsed
    outline.value = frontmatter.scenes
    saveState.value = { status: 'idle', lastSavedAt: frontmatter.last_modified_at, dirty: false }
  }

  function markDirty() {
    saveState.value = { ...saveState.value, dirty: true, status: 'saving' }
  }

  function markSaved() {
    saveState.value = { status: 'saved', lastSavedAt: new Date().toISOString(), dirty: false }
  }

  function addScene(scene) {
    scenes.value = [...scenes.value, scene]
    markDirty()
  }

  function openAI() { aiDrawerOpen.value = true }
  function closeAI() { aiDrawerOpen.value = false }
  function toggleAI() { aiDrawerOpen.value = !aiDrawerOpen.value }

  const totalWords = computed(() => scenes.value.reduce((sum, s) => sum + s.wordCount, 0))

  return {
    chapterId, mode, outline, scenes, annotations, aiDrawerOpen, writeGoal, saveState,
    toggleMode, load, markDirty, markSaved, addScene, openAI, closeAI, toggleAI,
    totalWords,
  }
})
