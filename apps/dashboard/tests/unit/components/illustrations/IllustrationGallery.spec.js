import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import IllustrationGallery from '@/components/illustrations/IllustrationGallery.vue'
import { useIllustrationStore } from '@/stores/useIllustrationStore'

describe('IllustrationGallery', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn().mockResolvedValue({ assets: [] })
  })

  it('renders 3-column grid of cards', async () => {
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', type: 'chapter', chapter_num: 1, style_preset: 'ink', url: '/x' },
      { id: 'b', type: 'chapter', chapter_num: 2, style_preset: 'ink', url: '/y' },
      { id: 'c', type: 'cover', chapter_num: null, style_preset: 'realistic', url: '/z' },
    ]

    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test' } })
    const cards = wrapper.findAll('[data-testid="illustration-card"]')
    expect(cards).toHaveLength(3)
  })

  it('filters by type when typeFilter prop set', async () => {
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', type: 'chapter', chapter_num: 1, style_preset: 'ink', url: '/x' },
      { id: 'c', type: 'cover', chapter_num: null, style_preset: 'realistic', url: '/z' },
    ]

    const wrapper = mount(IllustrationGallery, {
      props: { projectSlug: 'test', typeFilter: 'chapter' },
    })
    const cards = wrapper.findAll('[data-testid="illustration-card"]')
    expect(cards).toHaveLength(1)
    expect(cards[0].text()).toContain('第 1 章')
  })

  it('shows empty state when no assets', () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test' } })
    expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
  })
})