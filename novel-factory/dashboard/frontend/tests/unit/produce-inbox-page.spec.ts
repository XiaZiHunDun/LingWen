// tests/unit/produce-inbox-page.spec.ts — Phase B hub pages

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

const navMocks = vi.hoisted(() => ({
  produceTab: { value: 'studio' },
  inboxTab: { value: 'decisions' },
  setProduceTab: vi.fn(),
  setInboxTab: vi.fn(),
}))

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    produceTab: ref(navMocks.produceTab.value),
    inboxTab: ref(navMocks.inboxTab.value),
    setProduceTab: navMocks.setProduceTab,
    setInboxTab: navMocks.setInboxTab,
  }),
}))

vi.mock('../../src/pages/StudioPage.vue', () => ({
  default: { template: '<div data-testid="studio-embed">studio</div>' },
}))
vi.mock('../../src/pages/ChaptersPage.vue', () => ({
  default: { template: '<div data-testid="chapters-embed">chapters</div>' },
}))
vi.mock('../../src/pages/WorkflowsPage.vue', () => ({
  default: { template: '<div data-testid="workflows-embed">workflows</div>' },
}))
vi.mock('../../src/pages/DecisionsPage.vue', () => ({
  default: { template: '<div data-testid="decisions-embed">decisions</div>' },
}))
vi.mock('../../src/pages/RipplesPage.vue', () => ({
  default: { template: '<div data-testid="ripples-embed">ripples</div>' },
}))

import ProducePage from '../../src/pages/ProducePage.vue'
import InboxPage from '../../src/pages/InboxPage.vue'
import { byTestid } from '../helpers/by-testid'

describe('ProducePage (Phase B)', () => {
  beforeEach(() => {
    navMocks.produceTab.value = 'studio'
    vi.clearAllMocks()
  })

  test('renders hub title and studio tab by default', async () => {
    const wrapper = mount(ProducePage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('生产')
    expect(wrapper.find(byTestid('studio-embed')).exists()).toBe(true)
  })

  test('switching tab shows chapters embed', async () => {
    const wrapper = mount(ProducePage)
    await flushPromises()
    await wrapper.find(byTestid('produce-tabs-chapters')).trigger('click')
    expect(navMocks.setProduceTab).toHaveBeenCalledWith('chapters')
  })
})

describe('InboxPage (Phase B)', () => {
  beforeEach(() => {
    navMocks.inboxTab.value = 'decisions'
    vi.clearAllMocks()
  })

  test('renders hub title and decisions tab by default', async () => {
    const wrapper = mount(InboxPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('待办')
    expect(wrapper.find(byTestid('decisions-embed')).exists()).toBe(true)
  })

  test('switching tab calls setInboxTab', async () => {
    const wrapper = mount(InboxPage)
    await flushPromises()
    await wrapper.find(byTestid('inbox-tabs-ripples')).trigger('click')
    expect(navMocks.setInboxTab).toHaveBeenCalledWith('ripples')
  })
})
