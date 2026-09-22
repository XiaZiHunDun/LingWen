<script setup>
import { computed, onMounted, ref } from 'vue'
import { NCheckbox, NButton, NPopconfirm } from 'naive-ui'
import { useIllustration } from '@/composables/useIllustration'
import { useIllustrationStore } from '@/stores/useIllustrationStore'
import { useBulkDeleteToast } from '@/composables/useBulkDeleteToast'
import IllustrationCard from './IllustrationCard.vue'

const props = defineProps({
  projectSlug: { type: String, required: true },
  typeFilter: { type: String, default: null },  // 'cover' | 'chapter' | null
  // Phase 107: allow parent page to opt out of multi-select (e.g., empty preview).
  // Defaults to true so existing pages get multi-select for free.
  selectable: { type: Boolean, default: true },
})

const emit = defineEmits(['regenerate', 'delete', 'bulk-deleted'])

const { assets, error, loadAssets, regenerate, deleteAsset } = useIllustration(props.projectSlug)
const store = useIllustrationStore()
const toast = useBulkDeleteToast()

onMounted(() => loadAssets())

const filtered = computed(() => {
  if (!props.typeFilter) return assets.value
  return assets.value.filter(a => a.type === props.typeFilter)
})

// Phase 107: multi-select state. Component-local so selection survives asset
// prop changes (cross-page simulation). Vue 3 doesn't auto-track Set
// mutations, so we replace the Set reference on every change to trigger
// computed/template reactivity.
const selection = ref(new Set())
const bulkDeleteInFlight = ref(false)

const bulkActionBarVisible = computed(() => selection.value.size > 0)
const selectedCount = computed(() => selection.value.size)

function toggleSelect(assetId, checked) {
  if (checked) {
    selection.value.add(assetId)
  } else {
    selection.value.delete(assetId)
  }
  // Replace Set reference to force reactivity (Vue 3 doesn't auto-track Set mutations).
  selection.value = new Set(selection.value)
}

function clearSelection() {
  selection.value = new Set()
}

async function confirmBulkDelete() {
  if (bulkDeleteInFlight.value) return
  const ids = Array.from(selection.value)
  if (ids.length === 0) return
  bulkDeleteInFlight.value = true
  try {
    const result = await store.bulkDeleteAssets(props.projectSlug, ids)
    toast.showBulkDeleteResult(props.projectSlug, result)
    emit('bulk-deleted', result)
    clearSelection()
  } catch (e) {
    toast.showValidationError(e.message || 'bulk delete failed')
  } finally {
    bulkDeleteInFlight.value = false
  }
}

// Wrap async handlers so promise rejections bubble to the composable's
// `error` ref (surfaced via `error` below) rather than disappearing as
// unhandledrejection. The composable already sets `error` on failure.
function onRegenerate(id) {
  emit('regenerate', id)
  return regenerate(id)
}

function onDelete(id) {
  emit('delete', id)
  return deleteAsset(id)
}
</script>

<template>
  <div class="illustration-gallery" data-testid="illustration-gallery">
    <div v-if="filtered.length === 0" class="illustration-gallery-empty-state empty-state" data-testid="empty-state" role="status">
      尚未生成任何插图
    </div>
    <div v-else class="grid illustration-gallery-grid">
      <div
        v-for="asset in filtered"
        :key="asset.id"
        class="illustration-card-wrapper"
      >
        <NCheckbox
          v-if="selectable"
          :checked="selection.has(asset.id)"
          class="illustration-card__checkbox"
          :data-testid="`select-checkbox-${asset.id}`"
          @update:checked="(v) => toggleSelect(asset.id, v)"
        />
        <IllustrationCard
          :asset="asset"
          @regenerate="onRegenerate"
          @delete="onDelete"
        />
      </div>
    </div>

    <!-- Phase 107: sticky bottom bulk action bar (visible when selection > 0) -->
    <div
      v-if="bulkActionBarVisible"
      class="bulk-action-bar"
      data-testid="bulk-action-bar"
    >
      <span class="bulk-action-bar__count">已选 {{ selectedCount }} 张</span>
      <NButton
        data-testid="bulk-cancel-btn"
        class="bulk-cancel-btn"
        @click="clearSelection"
      >
        取消
      </NButton>
      <NPopconfirm
        positive-text="确认删除"
        negative-text="取消"
        @positive-click="confirmBulkDelete"
      >
        <template #trigger>
          <NButton
            type="error"
            :loading="bulkDeleteInFlight"
            data-testid="bulk-delete-btn"
            class="bulk-delete-btn"
          >
            🗑 批量删除
          </NButton>
        </template>
        确认删除这 {{ selectedCount }} 张插图？删除后无法恢复。
      </NPopconfirm>
    </div>
  </div>
</template>

<style scoped>
.illustration-gallery {
  padding: 16px;
}
.illustration-gallery-grid {
  display: grid;
  /* Responsive: auto-fill at min 220px wide cards; mobile gets 1 col,
     tablet 2 col, desktop 3+ col naturally without hardcoded breakpoints. */
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.illustration-gallery-empty {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-muted, #4b5563);
}

/* Phase 107: multi-select wrapper positions checkbox overlay at top-left of each card. */
.illustration-card-wrapper {
  position: relative;
}
.illustration-card__checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 2px;
}

/* Phase 107: sticky bottom bulk action bar. */
.bulk-action-bar {
  position: sticky;
  bottom: 0;
  z-index: 10;
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  background: var(--surface-elevated, #fafafa);
  border-top: 1px solid var(--border-color, #e5e5e5);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
}
.bulk-action-bar__count {
  font-weight: 600;
  margin-right: auto;
}
</style>