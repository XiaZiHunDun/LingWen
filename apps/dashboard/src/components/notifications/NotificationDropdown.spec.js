import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import NotificationDropdown from './NotificationDropdown.vue'
import { useNotificationStore } from '@/stores/useNotificationStore'

describe('NotificationDropdown', () => {
  it('renders empty state when history is empty', () => {
    setActivePinia(createPinia())
    const wrapper = mount(NotificationDropdown)
    expect(wrapper.text()).toContain('您还没有任何插图通知')
  })

  it('renders history list items when present', () => {
    setActivePinia(createPinia())
    const store = useNotificationStore()
    store.history = [
      { id: '01', projectSlug: 'p', eventType: 'generation', ts: '2026-09-18T07:00:00+00:00' },
      { id: '02', projectSlug: 'p', eventType: 'cleanup', ts: '2026-09-18T07:01:00+00:00' },
    ]
    const wrapper = mount(NotificationDropdown)
    expect(wrapper.findAll('[data-testid="notification-list-item"]')).toHaveLength(2)
  })
})