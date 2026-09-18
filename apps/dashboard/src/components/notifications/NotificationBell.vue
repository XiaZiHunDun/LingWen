<template>
  <div class="notification-bell-wrapper">
    <button class="bell" @click="open = !open" data-testid="notification-bell">
      <svg width="20" height="20" viewBox="0 0 256 256" fill="none" stroke="currentColor" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M56 104a72 72 0 0 1 144 0c0 35 8 53 16 64H40c8-11 16-29 16-64Z"/>
        <path d="M96 192a32 32 0 0 0 64 0"/>
      </svg>
      <span v-if="store.unreadCount > 0" class="badge" data-testid="notification-badge">
        {{ store.unreadCount > 99 ? '99+' : store.unreadCount }}
      </span>
      <span class="status-dot" :class="statusClass" data-testid="notification-status-dot" />
    </button>
    <NotificationDropdown v-if="open" @close="open = false" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useNotificationStore } from '@/stores/useNotificationStore'
import NotificationDropdown from './NotificationDropdown.vue'

const store = useNotificationStore()
const open = ref(false)

const statusClass = computed(() => ({
  'is-connected': store.isConnected,
  'is-error': store.lastError && !store.isConnected,
}))
</script>

<style scoped>
.notification-bell-wrapper { position: relative; display: inline-block; }
.bell {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text);
}
.bell:hover { background: var(--bg-muted); }
.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: var(--color-danger);
  color: white;
  font-size: 10px;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.status-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-dim);
}
.status-dot.is-connected { background: var(--color-success); }
.status-dot.is-error { background: var(--color-danger); }
</style>