import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NotificationListItem from './NotificationListItem.vue'

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
})