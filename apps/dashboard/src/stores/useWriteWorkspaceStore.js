import { defineStore } from 'pinia'
import { shallowRef, computed } from 'vue'
import { splitBodyIntoScenes, joinScenesToBody } from '@/utils/writeWorkspace/sceneParser.js'
import { countBodyWords } from '@/utils/writeWorkspace/wordCounter.js'

export const useWriteWorkspaceStore = defineStore('writeWorkspace', () => {
  const chapterId = shallowRef(null)
  const mode = shallowRef('author') // 'author' | 'editor'
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
