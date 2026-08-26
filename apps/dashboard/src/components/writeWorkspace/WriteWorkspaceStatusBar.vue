<template>
  <footer class="ws-status ws-status-bar" :data-status="saveState.status" data-testid="ws-status-bar">
    <span v-if="saveState.status === 'idle'">就绪</span>
    <span v-else-if="saveState.status === 'saving'">保存中…</span>
    <span v-else-if="saveState.status === 'saved'">
      已保存 {{ formatTime(saveState.lastSavedAt) }}
    </span>
    <span v-else-if="saveState.status === 'error'" class="ws-status--error">
      错误: {{ saveState.errorMessage || '未知' }}
      <button type="button" @click="$emit('retry')">重试</button>
    </span>
  </footer>
</template>

<script setup>
defineProps({
  saveState: { type: Object, required: true },
})
defineEmits(['retry'])

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.ws-status {
  padding: 0.5rem 1.5rem;
  border-top: 1px solid var(--n-border-color);
  font-size: 0.875rem;
  color: var(--n-text-color-3);
}
.ws-status--error { color: var(--n-error-color); }
</style>
