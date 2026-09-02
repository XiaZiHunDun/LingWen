<!--
  PilotCancelDialog.vue — Cancel batch 确认弹窗（P1）
-->
<template>
  <div
    v-if="visible"
    class="pilot-cancel-dialog"
    data-testid="pilot-cancel-dialog"
    role="dialog"
    aria-modal="true"
  >
    <div class="dialog-content pixel-card">
      <h3 class="dialog-title">确认取消 batch?</h3>
      <p class="dialog-body">
        Job <code>{{ jobId }}</code> 将收到 SIGTERM。5 秒未退出将自动 SIGKILL。
      </p>
      <p class="dialog-body">当前进度将丢失，是否继续？</p>
      <div class="dialog-actions">
        <button
          type="button"
          class="hold-btn pixel-border"
          data-testid="cancel-hold-btn"
          :disabled="loading"
          @click="emit('hold-on')"
        >
          {{ loading ? '取消中…' : '等一下' }}
        </button>
        <button
          type="button"
          class="confirm-btn pixel-border"
          data-testid="cancel-confirm-btn"
          :disabled="loading"
          @click="emit('confirm')"
        >
          {{ loading ? '取消中…' : '确认取消' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean; jobId: string; loading: boolean }>();
const emit = defineEmits<{
  confirm: [];
  'hold-on': [];
}>();
</script>

<style scoped>
.pilot-cancel-dialog {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog-content {
  padding: 1.5rem;
  max-width: 480px;
  background: var(--surface, #fff);
}
.dialog-title {
  margin: 0 0 1rem;
}
.dialog-body {
  margin: 0.5rem 0;
}
.dialog-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
}
.confirm-btn {
  background: var(--error-bg, #fee);
  color: var(--error, #c33);
  border-color: var(--error, #c33);
  padding: 0.4rem 0.8rem;
  cursor: pointer;
}
.hold-btn {
  padding: 0.4rem 0.8rem;
  cursor: pointer;
}
button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
