<template>
  <div class="notification-list-item" data-testid="notification-list-item">
    <span class="icon">{{ icon }}</span>
    <div class="body">
      <div class="title">{{ title }}</div>
      <div class="meta">{{ meta }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
})

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
</script>

<style scoped>
.notification-list-item {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
}
.icon { font-size: 18px; }
.body { flex: 1; min-width: 0; }
.title { font-weight: 500; }
.meta { color: var(--color-text-dim); font-size: var(--text-sm); }
</style>