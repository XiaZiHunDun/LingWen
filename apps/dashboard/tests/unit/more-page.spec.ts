// tests/unit/more-page.spec.ts — Task C-2
// MorePage coverage lift: 25% stmts / 28% lines / 0% functions → ~80%.
// Exercises: rendering, link clicks (with and without `tab`), creationMode injection.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, type Ref } from 'vue'
import MorePage from '../../src/pages/MorePage.vue'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  navigateTo: vi.fn(),
}))

// creationMode is injected via Vue provide — must be a Ref<unknown> so the
// page's `inject('creationMode', computed(...))` fallback unwraps it.
const creationModeRef: Ref<string> = ref('companion')

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    navigateTo: mocks.navigateTo,
  }),
}))

function mountMorePage() {
  return mount(MorePage, {
    global: {
      provide: {
        creationMode: creationModeRef,
      },
    },
  })
}

async function mountInMode(mode: string) {
  creationModeRef.value = mode
  const wrapper = mountMorePage()
  await flushPromises()
  return wrapper
}

describe('MorePage (Task C-2)', () => {
  beforeEach(() => {
    mocks.navigateTo.mockReset()
    creationModeRef.value = 'companion'
  })

  test('renders page testid', async () => {
    const wrapper = await mountInMode('companion')
    expect(wrapper.find(byTestid('more-page')).exists()).toBe(true)
  })

  test('companion mode renders today, inbox, insight only', async () => {
    const wrapper = await mountInMode('companion')

    expect(wrapper.find(byTestid('more-link-today')).exists()).toBe(true)
    expect(wrapper.find(byTestid('more-link-inbox')).exists()).toBe(true)
    expect(wrapper.find(byTestid('more-link-insight')).exists()).toBe(true)

    // produce and cascade-runs are NOT in companion mode
    expect(wrapper.find(byTestid('more-link-produce')).exists()).toBe(false)
    expect(wrapper.find(byTestid('more-link-cascade-runs')).exists()).toBe(false)
  })

  test('studio mode renders produce + cascade-runs', async () => {
    const wrapper = await mountInMode('studio')

    expect(wrapper.find(byTestid('more-link-today')).exists()).toBe(true)
    expect(wrapper.find(byTestid('more-link-produce')).exists()).toBe(true)
    expect(wrapper.find(byTestid('more-link-inbox')).exists()).toBe(true)
    expect(wrapper.find(byTestid('more-link-insight')).exists()).toBe(true)
    expect(wrapper.find(byTestid('more-link-cascade-runs')).exists()).toBe(true)
  })

  test('advance mode also renders produce + cascade-runs', async () => {
    const wrapper = await mountInMode('advance')

    expect(wrapper.find(byTestid('more-link-produce')).exists()).toBe(true)
    expect(wrapper.find(byTestid('more-link-cascade-runs')).exists()).toBe(true)
  })

  test('clicking a link without `tab` calls navigateTo with clearFocus', async () => {
    const wrapper = await mountInMode('companion')

    await wrapper.find(byTestid('more-link-today')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('today', { clearFocus: true })
  })

  test('clicking `produce` link passes tab: studio', async () => {
    const wrapper = await mountInMode('studio')

    await wrapper.find(byTestid('more-link-produce')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('produce', {
      tab: 'studio',
      clearFocus: true,
    })
  })

  test('clicking `inbox` link passes tab: decisions', async () => {
    const wrapper = await mountInMode('studio')

    await wrapper.find(byTestid('more-link-inbox')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('inbox', {
      tab: 'decisions',
      clearFocus: true,
    })
  })

  test('clicking `insight` link passes tab: overview', async () => {
    const wrapper = await mountInMode('studio')

    await wrapper.find(byTestid('more-link-insight')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('insight', {
      tab: 'overview',
      clearFocus: true,
    })
  })

  test('renders label, desc, and mark for each link card', async () => {
    const wrapper = await mountInMode('studio')

    const card = wrapper.find(byTestid('more-link-today'))
    expect(card.text()).toContain('今')  // mark
    expect(card.text()).toContain('今日概览')  // label
    expect(card.text()).toContain('任务、健康度与快捷入口')  // desc
  })

  test('falls back to companion mode for unknown creationMode', async () => {
    const wrapper = await mountInMode('unknown-mode')

    expect(wrapper.find(byTestid('more-link-cascade-runs')).exists()).toBe(false)
    expect(wrapper.find(byTestid('more-link-today')).exists()).toBe(true)
  })
})
