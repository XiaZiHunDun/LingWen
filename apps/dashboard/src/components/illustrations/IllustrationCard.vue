<script setup>
import { computed } from 'vue'
import { NPopconfirm } from 'naive-ui'

const props = defineProps({
  asset: { type: Object, required: true },
})

const emit = defineEmits(['regenerate', 'delete'])

const label = computed(() =>
  props.asset.type === 'cover' ? '封面' : `第 ${props.asset.chapter_num} 章`
)
</script>

<template>
  <div class="illustration-card" data-testid="illustration-card">
    <img
      :src="asset.url"
      :alt="label"
      class="thumb illustration-thumb"
      data-testid="illustration-thumb"
      loading="lazy"
    />
    <div class="meta">
      <span class="badge">{{ label }}</span>
      <span class="style">{{ asset.style_preset }}</span>
    </div>
    <div class="actions">
      <button
        class="regenerate-btn"
        data-testid="regenerate-btn"
        :aria-label="`重生 ${label}`"
        @click="emit('regenerate', asset.id)"
      >↻ 重生</button>
      <NPopconfirm
        positive-text="确认删除"
        negative-text="取消"
        @positive-click="emit('delete', asset.id)"
      >
        <template #trigger>
          <button
            class="delete-btn"
            data-testid="delete-btn"
            :aria-label="`删除 ${label}`"
          >🗑 删除</button>
        </template>
        确定删除这张插图？删除后无法恢复。
      </NPopconfirm>
    </div>
  </div>
</template>

<style scoped>
.illustration-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  overflow: hidden;
  background: var(--surface-elevated, #ffffff);
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
  color: var(--text-muted, #4b5563);
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
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 4px;
  background: transparent;
  color: inherit;
  cursor: pointer;
}
.actions button:hover {
  background: var(--bg-elevated, #f0ede6);
}
.actions button:focus-visible {
  outline: 2px solid var(--color-accent, #7c3aed);
  outline-offset: 2px;
}
</style>
