<template>
  <div
    class="notification-list-item"
    :class="{ 'is-deleted': item._deleted }"
    data-testid="notification-list-item"
  >
    <span class="icon">{{ icon }}</span>
    <div class="body">
      <div class="title">{{ title }}</div>
      <div class="meta">{{ meta }}</div>
      <div v-if="item._deleted" class="deleted-tag" data-testid="deleted-tag">
        资产已删除
      </div>
    </div>
    <NPopconfirm
      v-if="canDelete"
      positive-text="确认删除"
      negative-text="取消"
      @positive-click="onConfirmDelete"
    >
      <template #trigger>
        <button
          class="delete-btn"
          :class="{ 'touch-visible': isTouch }"
          :aria-label="`删除资产 ${item.assetId}`"
          data-testid="delete-btn"
          @click.stop
        >
          ✕
        </button>
      </template>
      <span>确认删除此资产？</span>
    </NPopconfirm>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { NPopconfirm } from 'naive-ui'
import { useNotificationStore } from '@/stores/useNotificationStore'
import { useDeleteFromNotificationToast } from '@/composables/useDeleteFromNotificationToast'

const props = defineProps({
  item: { type: Object, required: true },
})

const emit = defineEmits(['asset-deleted'])

const ICONS = {
  generation: '🖼',
  regeneration: '♻️',
  cleanup: '🧹',
  deletion: '🗑',
}

const LABELS = {
  generation: '生成',
  regeneration: '重生成',
  cleanup: '清理',
  deletion: '删除',
}

// Phase 109: eligibility for delete button (mirrors store action guard)
const canDelete = computed(() => {
  if (props.item._deleted) return false
  if (props.item.eventType !== 'generation' && props.item.eventType !== 'regeneration') {
    return false
  }
  return Boolean(props.item.assetId && props.item.projectSlug)
})

// Phase 109: touch detection — always-visible on touch devices (no hover)
const isTouch = ref(false)
onMounted(() => {
  // Guard: jsdom does not implement window.matchMedia (Phase 109 lesson)
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    isTouch.value = window.matchMedia('(hover: none)').matches
  }
})

const icon = computed(() => ICONS[props.item.eventType] ?? '•')
const title = computed(() => {
  const t = props.item
  const label = LABELS[t.eventType] ?? t.eventType
  if (t.assetType === 'cover') return `${label}封面`
  if (t.assetType === 'chapter') return `${label}插图 chapter ${t.chapterNum ?? '?'}`
  return label
})
const meta = computed(() => {
  const t = props.item
  const parts = []
  if (t.stylePreset) parts.push(t.stylePreset)
  if (t.provider) parts.push(t.provider)
  return parts.join(' · ')
})

// Phase 109: store action + toast dispatch + emit on success/not_found
const store = useNotificationStore()
const toast = useDeleteFromNotificationToast()

async function onConfirmDelete() {
  const result = await store.deleteAssetFromNotification(props.item)
  toast.showResult(result)
  if (result.status === 'deleted' || result.status === 'not_found') {
    emit('asset-deleted', props.item.id, props.item.assetId)
  }
  // status 'noop' | 'skipped' | 'error' — no emit (defensive against duplicate fires)
}

// Expose for test introspection (no-op in production)
defineExpose({ onConfirmDelete })
</script>

<style scoped>
.notification-list-item {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  position: relative;
}
.icon { font-size: 18px; }
.body { flex: 1; min-width: 0; }
.title { font-weight: 500; }
.meta { color: var(--color-text-dim); font-size: var(--text-sm); }

/* Phase 109: hover-revealed delete button (desktop) + always-visible (touch) */
.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-dim);
  padding: 2px 6px;
  font-size: var(--text-sm);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.notification-list-item:hover .delete-btn,
.delete-btn:focus-visible,
.delete-btn.touch-visible { opacity: 1; }
.delete-btn:hover { color: var(--color-danger); border-color: var(--color-danger); }

/* Phase 109: deleted state visual */
.is-deleted { opacity: 0.55; }
.is-deleted .delete-btn { display: none; }
.deleted-tag {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  font-style: italic;
  margin-top: 2px;
}
</style>