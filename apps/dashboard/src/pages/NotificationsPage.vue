<template>
  <div class="notifications-page">
    <h1>通知</h1>
    <nav class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="{ active: selectedTab === tab.key }"
        :data-testid="`tab-${tab.key}`"
        @click="selectedTab = tab.key"
      >
        {{ tab.label }}
        <span class="count">{{ countFor(tab.key) }}</span>
      </button>
    </nav>
    <div v-if="filtered.length === 0" class="empty">暂无通知</div>
    <div v-else class="list">
      <NotificationListItem v-for="item in filtered" :key="item.id" :item="item" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useNotificationStore } from '@/stores/useNotificationStore'
import NotificationListItem from '@/components/notifications/NotificationListItem.vue'

const store = useNotificationStore()
const { history } = storeToRefs(store)

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'generation', label: '生成' },
  { key: 'regeneration', label: '重生成' },
  { key: 'cleanup', label: '清理' },
  { key: 'deletion', label: '删除' },
]
const selectedTab = ref('all')

function countFor(key) {
  if (key === 'all') return history.value.length
  return history.value.filter((h) => h.eventType === key).length
}

const filtered = computed(() => {
  if (selectedTab.value === 'all') return history.value
  return history.value.filter((h) => h.eventType === selectedTab.value)
})
</script>

<style scoped>
.notifications-page { padding: 24px; }
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.tabs button {
  background: transparent;
  border: var(--border-width) solid var(--border-color);
  padding: 6px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
}
.tabs button.active { background: var(--color-accent-soft); border-color: var(--color-accent); }
.count {
  margin-left: 4px;
  color: var(--color-text-dim);
  font-size: var(--text-sm);
}
.empty { padding: 32px; text-align: center; color: var(--color-text-dim); }
</style>
