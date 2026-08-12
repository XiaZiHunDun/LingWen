<template>
  <div v-if="hasError" class="error-boundary" data-testid="error-boundary">
    <div class="error-boundary__content">
      <div class="error-boundary__icon">⚠️</div>
      <h2 class="error-boundary__title">页面加载异常</h2>
      <p class="error-boundary__message">{{ errorMessage }}</p>
      <div class="error-boundary__actions">
        <button class="error-boundary__btn" @click="handleRetry">
          🔄 刷新重试
        </button>
        <button class="error-boundary__btn error-boundary__btn--secondary" @click="handleShowDetails">
          {{ showDetails ? '收起详情' : '查看详情' }}
        </button>
      </div>
      <div v-if="showDetails" class="error-boundary__details">
        <pre class="error-boundary__stack">{{ errorStack }}</pre>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue';
import { logger } from '../utils/logger.js';

const hasError = ref(false);
const errorMessage = ref('');
const errorStack = ref('');
const showDetails = ref(false);

onErrorCaptured((error, instance, info) => {
  hasError.value = true;
  errorMessage.value = error.message || '未知错误';
  errorStack.value = `${error.message}\n\n组件: ${instance?.$options?.name || '未知'}\n位置: ${info}\n\n${error.stack || ''}`;
  
  logger.error('[ErrorBoundary] 捕获到组件错误:', error);
  
  return false;
});

function handleRetry() {
  hasError.value = false;
  showDetails.value = false;
  errorMessage.value = '';
  errorStack.value = '';
  window.location.reload();
}

function handleShowDetails() {
  showDetails.value = !showDetails.value;
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-primary);
  padding: var(--space-lg);
}

.error-boundary__content {
  max-width: 500px;
  width: 100%;
  text-align: center;
  padding: var(--space-xl);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-elegant);
}

.error-boundary__icon {
  font-size: 64px;
  margin-bottom: var(--space-md);
}

.error-boundary__title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-warning);
  margin-bottom: var(--space-sm);
}

.error-boundary__message {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-lg);
}

.error-boundary__actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
  margin-bottom: var(--space-md);
}

.error-boundary__btn {
  padding: 10px 24px;
  background: var(--color-accent);
  color: var(--color-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.error-boundary__btn:hover {
  background: var(--color-accent-hover);
  transform: translateY(-2px);
}

.error-boundary__btn--secondary {
  background: var(--bg-muted);
  color: var(--color-text-secondary);
}

.error-boundary__btn--secondary:hover {
  background: var(--border-color);
}

.error-boundary__details {
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-muted);
  border-radius: var(--radius-md);
  text-align: left;
}

.error-boundary__stack {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  line-height: 1.5;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>