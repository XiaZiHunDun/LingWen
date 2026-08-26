import { describe, it, afterEach, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

// Stub TimelineEditor to isolate toggle behavior
vi.mock('@/components/world/timeline/TimelineEditor.vue', () => ({
  default: {
    name: 'TimelineEditor',
    template: '<div data-testid="timeline-editor-stub" />',
  },
}))

import TimelineEventDetail from '@/components/world/timeline/TimelineEventDetail.vue'

const baseEvent = {
  id: 1,
  slug: 'first-awakening',
  title: '初醒',
  story_year: 1,
  story_label: '元年初',
  chapter: 'ch-01',
  description: '主角在山巅苏醒...',
}

describe('TimelineEventDetail — editing toggle', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('does not render TimelineEditor initially', () => {
    const wrapper = mount(TimelineEventDetail, { props: { event: baseEvent } })
    expect(wrapper.find('[data-testid="timeline-editor-stub"]').exists()).toBe(false)
  })

  it('renders toggle button labeled "新增事件" initially', () => {
    const wrapper = mount(TimelineEventDetail, { props: { event: baseEvent } })
    const btn = wrapper.find('[data-testid="timeline-event-detail-edit-toggle"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toBe('新增事件')
  })

  it('clicking the toggle renders TimelineEditor', async () => {
    const wrapper = mount(TimelineEventDetail, { props: { event: baseEvent } })
    await wrapper.find('[data-testid="timeline-event-detail-edit-toggle"]').trigger('click')
    await nextTick()
    expect(wrapper.find('[data-testid="timeline-editor-stub"]').exists()).toBe(true)
  })

  it('clicking the toggle a second time hides it; button label cycles back', async () => {
    const wrapper = mount(TimelineEventDetail, { props: { event: baseEvent } })
    const btn = wrapper.find('[data-testid="timeline-event-detail-edit-toggle"]')
    await btn.trigger('click')
    await nextTick()
    expect(wrapper.find('[data-testid="timeline-editor-stub"]').exists()).toBe(true)
    await btn.trigger('click')
    await nextTick()
    expect(wrapper.find('[data-testid="timeline-editor-stub"]').exists()).toBe(false)
    expect(btn.text()).toBe('新增事件')
  })
})