<template>
  <div class="workbench-root" data-testid="workbench-root">
    <WriteWorkspaceHeader
      :chapter-number="store.chapterId || 0"
      :title="currentTitle"
      :mode="store.mode"
      :total-words="store.totalWords"
      :daily-goal="writeGoal.dailyGoal.value"
      @toggle-mode="store.toggleMode"
    />

    <div class="workbench-root__body">
      <WriteWorkspaceOutlinePane
        :scenes="store.scenes"
        :active-scene-id="activeSceneId"
        @select-scene="activeSceneId = $event"
      />

      <div class="workbench-root__center">
        <WriteWorkspaceEditorPane
          :content="editorContent"
          :editable="true"
          @update:content="handleContentChange"
        />
      </div>

      <WriteWorkspaceAIDrawer
        :open="store.aiDrawerOpen"
        :context="aiContext"
        @close="store.closeAI"
      >
        <textarea
          v-model="chatInput"
          class="workbench-root__chat-input"
          placeholder="提示 AI 续写/修辞/场景建议…"
          rows="3"
        />
      </WriteWorkspaceAIDrawer>
    </div>

    <WriteWorkspaceStatusBar :save-state="store.saveState" @retry="retrySave" />

    <WriteInlineAnnotationLayer
      v-if="store.mode === 'editor'"
      :annotations="store.annotations"
      @jump-to-fix="handleJumpToFix"
    />

    <WriteWorkspaceConflictDialog
      :open="conflictDialogOpen"
      :external-mtime="conflictExternalMtime"
      @rebase="handleRebase"
      @discard="handleDiscard"
      @export="handleExportLocal"
    />
  </div>
</template>

<script setup>
/**
 * WriteWorkspacePage — Immersive Write Workspace v1 entry.
 *
 * Composes Header + OutlinePane + EditorPane + AIDrawer + StatusBar + AnnotationLayer.
 * Wires keyboard shortcuts (Cmd/Ctrl + . / 2 / 3 / s), mode persistence, and
 * debounced auto-save via the persistence composable.
 *
 * Note: the quality-check bridge (plan Task 23) is wired for editor-mode jumps.
 * The conflict-detection dialog (plan Task 24) is wired after loadChapter and
 * offers rebase / discard / export-local resolution.
 */
import { ref, computed, onMounted, onBeforeUnmount, watch as vueWatch } from 'vue'
import { useRoute } from 'vue-router'
import { useWriteWorkspaceStore } from '@/stores/useWriteWorkspaceStore'
import { useWriteWorkspaceApi } from '@/composables/useWriteWorkspaceApi'
import { useWriteWorkspacePersistence } from '@/composables/useWriteWorkspacePersistence'
import { useWriteGoal } from '@/composables/useWriteGoal'
import { useTypewriterMode } from '@/composables/useTypewriterMode'
import { useWriteQualityCheck } from '@/composables/useWriteQualityCheck'
import WriteWorkspaceHeader from '@/components/writeWorkspace/WriteWorkspaceHeader.vue'
import WriteWorkspaceOutlinePane from '@/components/writeWorkspace/WriteWorkspaceOutlinePane.vue'
import WriteWorkspaceEditorPane from '@/components/writeWorkspace/WriteWorkspaceEditorPane.vue'
import WriteWorkspaceAIDrawer from '@/components/writeWorkspace/WriteWorkspaceAIDrawer.vue'
import WriteWorkspaceStatusBar from '@/components/writeWorkspace/WriteWorkspaceStatusBar.vue'
import WriteInlineAnnotationLayer from '@/components/writeWorkspace/WriteInlineAnnotationLayer.vue'
import WriteWorkspaceConflictDialog from '@/components/writeWorkspace/WriteWorkspaceConflictDialog.vue'

const MODE_KEY = 'lingwen.write_workspace.mode'

const route = useRoute()
const store = useWriteWorkspaceStore()
const api = useWriteWorkspaceApi()
const writeGoal = useWriteGoal()
const typewriter = useTypewriterMode()
const quality = useWriteQualityCheck()

const editorContent = ref('')
const chatInput = ref('')
const activeSceneId = ref(null)
const conflictDialogOpen = ref(false)
const conflictExternalMtime = ref(0)

const persist = useWriteWorkspacePersistence({
  saveFn: api.saveChapter,
  debounceMs: 800,
})

const currentTitle = computed(() => store.outline[0]?.title || '无标题')

const aiContext = computed(() => {
  const scene = store.scenes.find(s => s.id === activeSceneId.value) || null
  return {
    current_chapter_heading: currentTitle.value,
    current_scene: scene?.title || '',
    current_scene_body: scene?.body || '',
    prev_chapter_tail: '',
    characters_in_scene: [],
  }
})

async function loadChapter() {
  const cid = Number(route.params.chapterId)
  try {
    const { frontmatter, body, mtime } = await api.loadChapter(cid)
    store.load({ chapterId: cid, frontmatter, body })
    editorContent.value = body
    await checkForConflict({ externalMtime: mtime })
  } catch (e) {
    // Backend not yet wired in v1; fall back to empty state so the page still renders.
    store.load({
      chapterId: cid,
      frontmatter: {
        chapter: cid,
        title: '新章节',
        scenes: [],
        total_words: 0,
        last_modified_by: 'human',
        last_modified_at: new Date().toISOString(),
      },
      body: '',
    })
    editorContent.value = ''
  }
}

async function checkForConflict({ externalMtime } = {}) {
  let serverMtime = externalMtime
  if (typeof serverMtime !== 'number') {
    try {
      const { mtime } = await api.loadChapter(store.chapterId)
      serverMtime = mtime
    } catch (e) {
      // Backend unavailable; skip conflict check.
      return
    }
  }
  const localMtime = persist.lastMtime.value || 0
  if (serverMtime > localMtime && store.saveState.dirty) {
    conflictExternalMtime.value = serverMtime
    conflictDialogOpen.value = true
  }
}

async function handleRebase() {
  conflictDialogOpen.value = false
  // Reload from server; discard local edits.
  await loadChapter()
}

function handleDiscard() {
  conflictDialogOpen.value = false
  // TODO: also clear dirty state and any pending saves.
}

async function handleExportLocal() {
  // TODO: write body to ch{N}.local.md via download anchor.
  conflictDialogOpen.value = false
}

function handleContentChange(html) {
  editorContent.value = html
  store.markDirty()
  persist.scheduleSave({
    chapterId: store.chapterId,
    frontmatter: {
      chapter: store.chapterId,
      title: currentTitle.value,
      scenes: store.outline,
      total_words: store.totalWords,
      last_modified_by: 'human',
      last_modified_at: new Date().toISOString(),
    },
    body: html,
  })
}

async function retrySave() {
  await persist.flushNow()
}

async function handleJumpToFix(annotation) {
  const result = await quality.runCheck({ chapterId: store.chapterId, body: editorContent.value })
  store.annotations = result.annotations
}

vueWatch(() => store.mode, async (newMode) => {
  if (newMode === 'editor' && store.chapterId) {
    try {
      const result = await quality.runCheck({ chapterId: store.chapterId, body: editorContent.value })
      store.annotations = result.annotations
    } catch (e) {
      console.warn('[write-workspace] quality check failed', e)
    }
  }
})

function handleKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === '.') {
    e.preventDefault()
    store.toggleMode()
  } else if ((e.metaKey || e.ctrlKey) && e.key === '2') {
    e.preventDefault()
    store.toggleAI()
  } else if ((e.metaKey || e.ctrlKey) && e.key === '3') {
    e.preventDefault()
    typewriter.toggle()
  } else if ((e.metaKey || e.ctrlKey) && e.key === 's') {
    e.preventDefault()
    persist.flushNow()
  }
}

onMounted(() => {
  const savedMode = localStorage.getItem(MODE_KEY)
  if (savedMode === 'author' || savedMode === 'editor') {
    store.mode = savedMode
  }
  loadChapter()
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  localStorage.setItem(MODE_KEY, store.mode)
  persist.flushNow()
})
</script>

<style scoped>
.workbench-root {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.workbench-root__body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.workbench-root__center {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.workbench-root__chat-input {
  width: 100%;
  border: 1px solid var(--n-border-color);
  border-radius: 4px;
  padding: 0.5rem;
  font-family: inherit;
  margin-top: 1rem;
  resize: vertical;
}
</style>
