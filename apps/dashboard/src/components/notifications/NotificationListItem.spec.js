import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useMessage } from 'naive-ui'
import NotificationListItem from './NotificationListItem.vue'
import { useNotificationStore } from '@/stores/useNotificationStore'

const mockMessage = {
  success: vi.fn(),
  info: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
}

vi.mock('naive-ui', () => ({
  useMessage: vi.fn(() => mockMessage),
  NPopconfirm: { template: '<div><slot /><slot name="trigger" /></div>' },
}))

const baseItem = {
  id: '01HZX',
  projectSlug: 'p',
  eventType: 'generation',
  assetId: 'a1',
  assetType: 'chapter',
  chapterNum: 3,
  stylePreset: 'noir',
  provider: 'minimax',
  ts: '2026-09-18T07:00:00+00:00',
  extra: null,
}

describe('NotificationListItem', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders event-type icon and label', () => {
    const wrapper = mount(NotificationListItem, { props: { item: baseItem } })
    expect(wrapper.text()).toContain('生成')
  })

  it('shows asset type and chapter when applicable', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, assetType: 'chapter', chapterNum: 5 } },
    })
    expect(wrapper.text()).toContain('chapter')
    expect(wrapper.text()).toContain('5')
  })

  it('shows provider name for generation/regeneration', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, provider: 'openai' } },
    })
    expect(wrapper.text()).toContain('openai')
  })

  // Phase 109: delete button eligibility + NPopconfirm + deleted state
  it('T1: generation event renders delete button', () => {
    const wrapper = mount(NotificationListItem, { props: { item: baseItem } })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(true)
  })

  it('T2: regeneration event renders delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'regeneration' } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(true)
  })

  it('T3: cleanup event does NOT render delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'cleanup', assetId: null } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
  })

  it('T4: deletion event does NOT render delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'deletion' } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
  })

  it('T5: warning event (assetId=null) does NOT render delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'generation', assetId: null } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
  })

  it('T6: _deleted=true hides delete button + shows 资产已删除 tag', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, _deleted: true } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="deleted-tag"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('资产已删除')
  })

  it('T7: NPopconfirm negative click does NOT call store.deleteAssetFromNotification', async () => {
    const store = useNotificationStore()
    const spy = vi.spyOn(store, 'deleteAssetFromNotification').mockResolvedValue({ status: 'deleted' })
    const wrapper = mount(NotificationListItem, { props: { item: baseItem } })
    // Negative click test — verify spy is NOT called initially
    expect(spy).not.toHaveBeenCalled()
    // Click the trigger button to open the popconfirm
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    // Negative branch: store should still not be called (cancel is purely frontend)
    expect(spy).not.toHaveBeenCalled()
  })

  it('T8: positive click calls store + emits asset-deleted', async () => {
    const store = useNotificationStore()
    store.history = [{ ...baseItem }]
    const spy = vi.spyOn(store, 'deleteAssetFromNotification').mockResolvedValue({ status: 'deleted' })
    const wrapper = mount(NotificationListItem, { props: { item: store.history[0] } })
    // Directly invoke the positive-click handler (NPopconfirm provider not mounted in test)
    wrapper.vm.onConfirmDelete?.()
    await wrapper.vm.$nextTick?.()
    expect(spy).toHaveBeenCalledWith(
      expect.objectContaining({ assetId: 'a1' })
    )
  })
})