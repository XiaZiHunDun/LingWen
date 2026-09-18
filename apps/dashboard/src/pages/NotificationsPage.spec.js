import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import NotificationsPage from './NotificationsPage.vue'
import { useNotificationStore } from '@/stores/useNotificationStore'

describe('NotificationsPage', () => {
  it('renders tabs for all four event types', () => {
    setActivePinia(createPinia())
    const wrapper = mount(NotificationsPage)
    expect(wrapper.text()).toContain('全部')
    expect(wrapper.text()).toContain('生成')
    expect(wrapper.text()).toContain('重生成')
    expect(wrapper.text()).toContain('清理')
  })

  it('filters history by selected event type tab', async () => {
    setActivePinia(createPinia())
    const store = useNotificationStore()
    store.history = [
      { id: '01', projectSlug: 'p', eventType: 'generation', ts: '2026-09-18T07:00:00+00:00' },
      { id: '02', projectSlug: 'p', eventType: 'cleanup', ts: '2026-09-18T07:01:00+00:00' },
      { id: '03', projectSlug: 'p', eventType: 'generation', ts: '2026-09-18T07:02:00+00:00' },
    ]
    const wrapper = mount(NotificationsPage)
    await wrapper.find('[data-testid="tab-cleanup"]').trigger('click')
    const items = wrapper.findAll('[data-testid="notification-list-item"]')
    expect(items).toHaveLength(1)
  })
})
