<script setup>
const props = defineProps({
  asset: { type: Object, required: true },
  projectSlug: { type: String, required: true },
})

const emit = defineEmits(['regenerate', 'delete'])

const label = props.asset.type === 'cover' ? '封面' : `第 ${props.asset.chapter_num} 章`
</script>

<template>
  <div class="illustration-card" data-testid="illustration-card">
    <img
      :src="asset.url"
      :alt="label"
      class="thumb"
      data-testid="illustration-thumb"
      loading="lazy"
    />
    <div class="meta">
      <span class="badge">{{ label }}</span>
      <span class="style">{{ asset.style_preset }}</span>
    </div>
    <div class="actions">
      <button data-testid="regenerate-btn" @click="emit('regenerate', asset.id)">↻ 重生</button>
      <button data-testid="delete-btn" @click="emit('delete', asset.id)">🗑 删除</button>
    </div>
  </div>
</template>

<style scoped>
.illustration-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border, #2a2a3a);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-surface, #14141e);
}
.thumb {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  display: block;
}
.meta {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  font-size: 12px;
}
.actions {
  display: flex;
  gap: 4px;
  padding: 0 8px 8px;
}
.actions button {
  flex: 1;
  font-size: 12px;
  padding: 6px 8px;
  border: 1px solid var(--color-border, #2a2a3a);
  border-radius: 4px;
  background: transparent;
  color: var(--color-text, #d0d0e0);
  cursor: pointer;
}
.actions button:hover {
  background: var(--color-hover, #2a2a3a);
}
</style>
