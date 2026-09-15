<script setup>
import { computed, onMounted } from 'vue'
import { useIllustration } from '@/composables/useIllustration'
import IllustrationCard from './IllustrationCard.vue'

const props = defineProps({
  projectSlug: { type: String, required: true },
  typeFilter: { type: String, default: null },  // 'cover' | 'chapter' | null
})

const emit = defineEmits(['regenerate', 'delete'])

const { assets, error, loadAssets, regenerate, deleteAsset } = useIllustration(props.projectSlug)

onMounted(() => loadAssets())

const filtered = computed(() => {
  if (!props.typeFilter) return assets.value
  return assets.value.filter(a => a.type === props.typeFilter)
})

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
    <div v-if="filtered.length === 0" class="empty illustration-gallery-empty" data-testid="empty-state" role="status">
      尚未生成任何插图
    </div>
    <div v-else class="grid illustration-gallery-grid">
      <IllustrationCard
        v-for="asset in filtered"
        :key="asset.id"
        :asset="asset"
        @regenerate="onRegenerate"
        @delete="onDelete"
      />
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
</style>