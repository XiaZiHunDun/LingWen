<template>
  <div v-if="open" class="ws-conflict-dialog" data-testid="conflict-dialog">
    <div class="ws-conflict-dialog__backdrop" />
    <div class="ws-conflict-dialog__panel">
      <h3>检测到外部修改</h3>
      <p>外部时间戳: {{ externalMtime }}</p>
      <div class="ws-conflict-dialog__actions">
        <button data-testid="rebase-btn" @click="$emit('rebase')">Rebase 他们的到本地</button>
        <button data-testid="discard-btn" @click="$emit('discard')">放弃本地</button>
        <button data-testid="export-btn" @click="$emit('export')">导出本地到 .local.md</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  open: { type: Boolean, required: true },
  externalMtime: { type: Number, default: 0 },
})

defineEmits(['rebase', 'discard', 'export'])
</script>

<style scoped>
.ws-conflict-dialog { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; }
.ws-conflict-dialog__backdrop { position: absolute; inset: 0; background: rgba(0,0,0,0.5); }
.ws-conflict-dialog__panel { position: relative; background: var(--n-color); padding: 2rem; border-radius: 8px; min-width: 400px; }
.ws-conflict-dialog__actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
</style>