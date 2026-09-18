<template>
  <div class="notification-dropdown" data-testid="notification-dropdown">
    <header>
      <h3>通知 ({{ store.unreadCount }})</h3>
      <button v-if="store.unreadCount > 0" @click="store.markAllRead()">全部已读</button>
    </header>
    <div v-if="store.isConnected === false && store.lastError" class="error-banner" data-testid="notification-error">
      {{ store.lastError }}
    </div>
    <div v-if="items.length === 0" class="empty" data-testid="notification-empty">
      您还没有任何插图通知
    </div>
    <div v-else class="list">
      <NotificationListItem v-for="item in items" :key="item.id" :item="item" />
    </div>
    <footer>
      <router-link to="/notifications">查看全部 →</router-link>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useNotificationStore } from '@/stores/useNotificationStore'
import NotificationListItem from './NotificationListItem.vue'

const store = useNotificationStore()
const { history } = storeToRefs(store)
const items = computed(() => history.value.slice(0, 20))
</script>

<style scoped>
.notification-dropdown {
  width: 360px;
  max-height: 480px;
  display: flex;
  flex-direction: column;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-elegant);
  overflow: hidden;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}
.error-banner {
  padding: 8px 16px;
  background: var(--color-warning-soft);
  color: var(--color-warning);
  font-size: var(--text-sm);
}
.empty {
  padding: 32px 16px;
  text-align: center;
  color: var(--color-text-dim);
}
.list { flex: 1; overflow-y: auto; }
footer {
  padding: 8px 16px;
  border-top: 1px solid var(--border-color);
  text-align: center;
}
</style>