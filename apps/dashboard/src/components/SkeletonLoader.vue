<template>
  <div class="skeleton-loader" :class="{ 'skeleton-loader--page': page }">
    <template v-if="page === 'write'">
      <div class="skeleton__header">
        <div class="skeleton__avatar"></div>
        <div class="skeleton__title-row">
          <div class="skeleton__title"></div>
          <div class="skeleton__badge"></div>
        </div>
      </div>
      <div class="skeleton__body">
        <div class="skeleton__sidebar">
          <div class="skeleton__section">
            <div class="skeleton__section-title"></div>
            <div class="skeleton__list">
              <div v-for="i in 5" :key="i" class="skeleton__list-item"></div>
            </div>
          </div>
          <div class="skeleton__section">
            <div class="skeleton__section-title"></div>
            <div class="skeleton__input"></div>
            <div class="skeleton__tags">
              <div v-for="i in 4" :key="i" class="skeleton__tag"></div>
            </div>
          </div>
          <div class="skeleton__section">
            <div class="skeleton__section-title"></div>
            <div v-for="i in 2" :key="i" class="skeleton__text-line"></div>
          </div>
        </div>
        <div class="skeleton__editor">
          <div v-for="i in 8" :key="i" class="skeleton__paragraph">
            <div class="skeleton__line"></div>
            <div class="skeleton__line"></div>
            <div class="skeleton__line"></div>
          </div>
        </div>
      </div>
      <div class="skeleton__footer">
        <div class="skeleton__progress"></div>
        <div class="skeleton__buttons">
          <div class="skeleton__btn skeleton__btn--primary"></div>
          <div class="skeleton__btn"></div>
          <div class="skeleton__btn"></div>
        </div>
      </div>
    </template>

    <template v-else-if="page === 'library'">
      <div class="skeleton__header">
        <div class="skeleton__title"></div>
        <div class="skeleton__btn skeleton__btn--primary"></div>
      </div>
      <div class="skeleton__grid">
        <div v-for="i in 6" :key="i" class="skeleton__card">
          <div class="skeleton__card-cover"></div>
          <div class="skeleton__card-body">
            <div class="skeleton__card-title"></div>
            <div class="skeleton__card-subtitle"></div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="page === 'ask'">
      <div class="skeleton__panel">
        <div class="skeleton__lead-bar"></div>
        <div class="skeleton__messages">
          <div v-for="i in 3" :key="i" class="skeleton__message">
            <div class="skeleton__message-avatar"></div>
            <div class="skeleton__message-body">
              <div v-for="j in 3" :key="j" class="skeleton__message-line"></div>
            </div>
          </div>
        </div>
        <div class="skeleton__composer">
          <div class="skeleton__hints">
            <div v-for="i in 3" :key="i" class="skeleton__hint"></div>
          </div>
          <div class="skeleton__input-large"></div>
          <div class="skeleton__send-btn"></div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="skeleton__generic">
        <div class="skeleton__hero">
          <div class="skeleton__hero-title"></div>
          <div class="skeleton__hero-subtitle"></div>
        </div>
        <div class="skeleton__content">
          <div v-for="i in 4" :key="i" class="skeleton__card"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  page: {
    type: String,
    default: null,
  },
});
</script>

<style scoped>
.skeleton-loader {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
}

.skeleton-loader--page {
  padding: 0;
}

.skeleton__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.skeleton__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
}

.skeleton__title-row {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-left: var(--space-md);
}

.skeleton__title {
  height: 24px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__header .skeleton__title {
  width: 200px;
}

.skeleton__badge {
  width: 60px;
  height: 24px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 12px;
}

.skeleton__body {
  flex: 1;
  display: flex;
  background: var(--bg-primary);
}

.skeleton__sidebar {
  width: 280px;
  flex-shrink: 0;
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton__section {
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.skeleton__section-title {
  height: 18px;
  width: 80px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.skeleton__list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton__list-item {
  height: 36px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__input {
  height: 40px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.skeleton__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skeleton__tag {
  width: 50px;
  height: 24px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 12px;
}

.skeleton__text-line {
  height: 16px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
}

.skeleton__text-line:last-child {
  width: 70%;
}

.skeleton__editor {
  flex: 1;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton__paragraph {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton__line {
  height: 20px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__line:nth-child(2) {
  width: 90%;
}

.skeleton__line:nth-child(3) {
  width: 70%;
}

.skeleton__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-elevated);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.skeleton__progress {
  height: 18px;
  width: 150px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__buttons {
  display: flex;
  gap: var(--space-sm);
}

.skeleton__btn {
  height: 40px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-md);
}

.skeleton__btn:first-child {
  width: 100px;
}

.skeleton__btn:not(:first-child) {
  width: 70px;
}

.skeleton__btn--primary {
  background: linear-gradient(90deg, var(--color-accent-soft) 25%, var(--color-accent-muted) 50%, var(--color-accent-soft) 75%);
}

.skeleton__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-md);
  padding: var(--space-lg);
}

.skeleton__card {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
}

.skeleton__card-cover {
  width: 64px;
  height: 80px;
  background: linear-gradient(90deg, var(--color-accent-soft) 25%, var(--color-accent-muted) 50%, var(--color-accent-soft) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-md);
}

.skeleton__card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton__card-title {
  height: 20px;
  width: 80%;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__card-subtitle {
  height: 16px;
  width: 60%;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
}

.skeleton__lead-bar {
  height: 32px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton__message {
  display: flex;
  gap: var(--space-sm);
}

.skeleton__message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
}

.skeleton__message-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton__message-line {
  height: 18px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__message-line:nth-child(2) {
  width: 80%;
}

.skeleton__message-line:nth-child(3) {
  width: 60%;
}

.skeleton__composer {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton__hints {
  display: flex;
  gap: 8px;
}

.skeleton__hint {
  height: 28px;
  width: 80px;
  background: linear-gradient(90deg, var(--color-accent-soft) 25%, var(--color-accent-muted) 50%, var(--color-accent-soft) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 14px;
}

.skeleton__input-large {
  height: 56px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 20px;
}

.skeleton__send-btn {
  width: 36px;
  height: 36px;
  margin-left: auto;
  background: linear-gradient(90deg, var(--color-accent) 25%, var(--color-accent-hover) 50%, var(--color-accent) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 50%;
}

.skeleton__generic {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding: var(--space-lg);
}

.skeleton__hero {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton__hero-title {
  height: 36px;
  width: 40%;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__hero-subtitle {
  height: 18px;
  width: 30%;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-color) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton__content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-md);
}

.skeleton__generic .skeleton__card {
  padding: var(--space-lg);
  gap: var(--space-md);
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
