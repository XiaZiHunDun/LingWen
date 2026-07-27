<template>
  <div class="toast-container" data-testid="toast-container">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="`toast--${toast.type}`"
        @click="removeToast(toast.id)"
      >
        <span class="toast__icon">{{ getIcon(toast.type) }}</span>
        <span class="toast__message">{{ toast.message }}</span>
        <button class="toast__close" @click.stop="removeToast(toast.id)">✕</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide } from 'vue';

const toasts = ref([]);
let toastId = 0;
let timeoutIds = new Map();

function getIcon(type) {
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ',
  };
  return icons[type] || 'ℹ';
}

function addToast(message, type = 'info', duration = 3000) {
  const id = ++toastId;
  toasts.value.push({ id, message, type });
  
  if (duration > 0) {
    const timeoutId = setTimeout(() => {
      removeToast(id);
    }, duration);
    timeoutIds.set(id, timeoutId);
  }
  
  return id;
}

function removeToast(id) {
  const index = toasts.value.findIndex(t => t.id === id);
  if (index > -1) {
    toasts.value.splice(index, 1);
    const timeoutId = timeoutIds.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutIds.delete(id);
    }
  }
}

function success(message, duration = 3000) {
  return addToast(message, 'success', duration);
}

function error(message, duration = 5000) {
  return addToast(message, 'error', duration);
}

function warning(message, duration = 4000) {
  return addToast(message, 'warning', duration);
}

function info(message, duration = 3000) {
  return addToast(message, 'info', duration);
}

function clearAll() {
  toasts.value.forEach(toast => {
    const timeoutId = timeoutIds.get(toast.id);
    if (timeoutId) clearTimeout(timeoutId);
  });
  toasts.value = [];
  timeoutIds.clear();
}

const toastApi = {
  add: addToast,
  success,
  error,
  warning,
  info,
  remove: removeToast,
  clear: clearAll,
};

provide('toast', toastApi);

onUnmounted(() => {
  timeoutIds.forEach(id => clearTimeout(id));
});
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-elegant);
  border: var(--border-width) solid var(--border-color);
  min-width: 280px;
  max-width: 420px;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.toast:hover {
  transform: translateX(-4px);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.12);
}

.toast--success {
  border-color: var(--color-success);
  background: linear-gradient(135deg, var(--color-success-soft) 0%, var(--bg-elevated) 100%);
}

.toast--success .toast__icon {
  color: var(--color-success);
}

.toast--error {
  border-color: var(--color-danger);
  background: linear-gradient(135deg, var(--color-danger-soft) 0%, var(--bg-elevated) 100%);
}

.toast--error .toast__icon {
  color: var(--color-danger);
}

.toast--warning {
  border-color: var(--color-warning);
  background: linear-gradient(135deg, var(--color-warning-soft) 0%, var(--bg-elevated) 100%);
}

.toast--warning .toast__icon {
  color: var(--color-warning);
}

.toast--info {
  border-color: var(--color-accent);
  background: linear-gradient(135deg, var(--color-accent-soft) 0%, var(--bg-elevated) 100%);
}

.toast--info .toast__icon {
  color: var(--color-accent);
}

.toast__icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.toast__message {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: 1.5;
}

.toast__close {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-dim);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.toast__close:hover {
  background: var(--bg-muted);
  color: var(--color-text);
}

.toast-enter-active {
  animation: toast-in 0.3s ease-out;
}

.toast-leave-active {
  animation: toast-out 0.25s ease-in;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(100%);
    max-height: 0;
  }
  to {
    opacity: 1;
    transform: translateX(0);
    max-height: 100px;
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(0);
    max-height: 100px;
  }
  to {
    opacity: 0;
    transform: translateX(100%);
    max-height: 0;
  }
}
</style>
