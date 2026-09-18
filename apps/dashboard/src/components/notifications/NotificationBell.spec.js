import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import NotificationBell from './NotificationBell.vue'
import { useNotificationStore } from '@/stores/useNotificationStore'

describe('NotificationBell', () => {
  it('hides badge when unreadCount is 0', () => {
    setActivePinia(createPinia())
    const wrapper = mount(NotificationBell)
    expect(wrapper.find('[data-testid="notification-badge"]').exists()).toBe(false)
  })

  it('shows badge with count when unreadCount > 0', () => {
    setActivePinia(createPinia())
    const store = useNotificationStore()
    store.unreadCount = 5
    const wrapper = mount(NotificationBell)
    const badge = wrapper.find('[data-testid="notification-badge"]')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('5')
  })

  it('caps badge at 99+', () => {
    setActivePinia(createPinia())
    const store = useNotificationStore()
    store.unreadCount = 200
    const wrapper = mount(NotificationBell)
    expect(wrapper.find('[data-testid="notification-badge"]').text()).toBe('99+')
  })
})