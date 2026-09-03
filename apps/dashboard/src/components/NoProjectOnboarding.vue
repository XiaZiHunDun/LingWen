<template>
  <div class="onboarding no-project-onboarding" data-testid="no-project-onboarding">
    <div class="onboarding__card onboarding-card" data-testid="onboarding-card">
      <img src="/assets/brand/moling-logo.jpg" alt="墨灵Logo" class="onboarding__logo" aria-hidden="true" />

      <div class="onboarding__head">
        <h1 class="onboarding__title">{{ BRAND.productNameZh }}</h1>
        <p class="onboarding__tagline">{{ BRAND.productTagline }}</p>
      </div>

      <p v-if="loading" class="onboarding__hint onboarding-loading" data-testid="onboarding-loading">
        <span class="onboarding__spinner" aria-hidden="true" />
        正在检查项目…
      </p>

      <template v-else-if="error">
        <p class="onboarding__error onboarding-error" data-testid="onboarding-error">无法连接到后端：{{ error }}</p>
        <button type="button" class="onboarding__btn" @click="$emit('refresh')">重试</button>
      </template>

      <template v-else>
        <p class="onboarding__intro">
          这是 {{ BRAND.productNameZh }}。它是一个<b>本地优先</b>的 AI 小说创作工作台——
          你的小说项目由一组章节/设定文件构成，需要先在本机初始化一个项目，再在这里浏览与创作。
        </p>

        <div class="onboarding__section">
          <div class="onboarding__section-title">还没有项目，就这样开始</div>
          <ol class="onboarding__steps">
            <li>
              <div class="onboarding__step-desc">在本机初始化一本新书（书名与主角可自拟）</div>
              <pre class="onboarding__code onboarding-cmd-init" data-testid="onboarding-cmd-init">python lingwen.py init-project my-book --title "书名" --protagonist 主角</pre>
            </li>
            <li>
              <div class="onboarding__step-desc">让后端读到这本新书，再回到这里刷新</div>
              <pre class="onboarding__code onboarding-cmd-env" data-testid="onboarding-cmd-env">export LINGWEN_PROJECT_ROOT="$(pwd)/projects/my-book"</pre>
            </li>
          </ol>
        </div>

        <div class="onboarding__actions">
          <button type="button" class="onboarding__btn onboarding__btn--primary" @click="$emit('refresh')">
            我已准备好项目，刷新
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { BRAND } from '@/config/brand';

defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
});

defineEmits(['refresh']);
</script>

<style scoped>
.onboarding {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: radial-gradient(circle at 20% 10%, var(--color-accent-soft) 0%, transparent 45%),
    var(--bg-primary);
}

.onboarding__card {
  width: 100%;
  max-width: 560px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg, 16px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.onboarding__logo {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md, 12px);
  object-fit: cover;
}

.onboarding__head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.onboarding__title {
  margin: 0;
  font-size: 26px;
  font-family: var(--font-heading);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.onboarding__tagline {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-dim);
}

.onboarding__intro {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.onboarding__section {
  background: var(--bg-muted);
  border-radius: var(--radius-md, 12px);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.onboarding__section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-dim);
  letter-spacing: 0.02em;
}

.onboarding__steps {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
  counter-reset: step;
}

.onboarding__steps li {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.onboarding__step-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.onboarding__step-desc::before {
  counter-increment: step;
  content: counter(step);
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-accent);
  background: var(--color-accent);
  border-radius: 50%;
}

.onboarding__code {
  margin: 0;
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: var(--color-text);
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 10px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.onboarding__actions {
  display: flex;
  justify-content: flex-start;
}

.onboarding__btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  background: var(--bg-muted);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md, 10px);
  cursor: pointer;
  transition: all 0.15s ease;
}

.onboarding__btn:hover {
  border-color: var(--color-accent);
}

.onboarding__btn--primary {
  color: var(--color-on-accent);
  background: var(--color-accent);
  border-color: transparent;
}

.onboarding__btn--primary:hover {
  filter: brightness(1.05);
}

.onboarding__error {
  margin: 0;
  font-size: 13px;
  color: var(--color-danger, #d43);
}

.onboarding__hint {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-dim);
}

.onboarding__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border-color);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: onboarding-spin 0.8s linear infinite;
}

@keyframes onboarding-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>