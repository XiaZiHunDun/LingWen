<template>
  <aside
    class="ws-ai-drawer"
    :class="{ 'is-closed': !open }"
    data-testid="ai-drawer"
  >
    <header class="ws-ai-drawer__header">
      <button
        type="button"
        class="ws-ai-drawer__close"
        data-testid="close-btn"
        @click="$emit('close')"
      >✕</button>
      <h3>AI 协作</h3>
    </header>
    <WriteChatContextInjector :context="context" />
    <slot />
  </aside>
</template>

<script setup>
import WriteChatContextInjector from './WriteChatContextInjector.vue'

defineProps({
  open: { type: Boolean, required: true },
  context: { type: Object, required: true },
})

defineEmits(['close'])
</script>

<style scoped>
.ws-ai-drawer {
  width: 320px;
  border-left: 1px solid var(--n-border-color);
  padding: 1rem;
  overflow-y: auto;
  transition: width 0.2s;
}
.ws-ai-drawer.is-closed {
  width: 0;
  padding: 0;
  border-left: none;
  overflow: hidden;
}
.ws-ai-drawer__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.ws-ai-drawer__close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
}
</style>