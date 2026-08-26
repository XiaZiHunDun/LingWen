import { describe, it, afterEach, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

// Stub LoreEditor to isolate toggle behavior from useWorldReview
vi.mock('@/components/world/lore/LoreEditor.vue', () => ({
  default: {
    name: 'LoreEditor',
    template: '<div data-testid="lore-editor-stub" />',
  },
}))

import LoreDetail from '@/components/world/lore/LoreDetail.vue'

const baseLore = {
  id: 1,
  slug: 'magic-system',
  title: '魔网',
  category: 'magic_system',
  summary: '',
  body: '魔网是...',
}

describe('LoreDetail — editing toggle', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('does not render LoreEditor initially', () => {
    const wrapper = mount(LoreDetail, { props: { lore: baseLore } })
    expect(wrapper.find('[data-testid="lore-editor-stub"]').exists()).toBe(false)
  })

  it('renders toggle button labeled "新增条目" initially', () => {
    const wrapper = mount(LoreDetail, { props: { lore: baseLore } })
    const btn = wrapper.find('[data-testid="lore-detail-edit-toggle"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toBe('新增条目')
  })

  it('clicking the toggle renders LoreEditor', async () => {
    const wrapper = mount(LoreDetail, { props: { lore: baseLore } })
    await wrapper.find('[data-testid="lore-detail-edit-toggle"]').trigger('click')
    await nextTick()
    expect(wrapper.find('[data-testid="lore-editor-stub"]').exists()).toBe(true)
  })

  it('clicking the toggle a second time hides it; button label cycles back', async () => {
    const wrapper = mount(LoreDetail, { props: { lore: baseLore } })
    const btn = wrapper.find('[data-testid="lore-detail-edit-toggle"]')
    await btn.trigger('click')
    await nextTick()
    expect(wrapper.find('[data-testid="lore-editor-stub"]').exists()).toBe(true)
    await btn.trigger('click')
    await nextTick()
    expect(wrapper.find('[data-testid="lore-editor-stub"]').exists()).toBe(false)
    expect(btn.text()).toBe('新增条目')
  })
})