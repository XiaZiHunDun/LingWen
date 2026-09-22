import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import IllustrationGallery from '@/components/illustrations/IllustrationGallery.vue'
import { useIllustrationStore } from '@/stores/useIllustrationStore'

// Phase 107 M6: stub the toast composable so F7/F8 don't depend on Naive UI's
// <n-message-provider> being mounted. The actual toast rendering is covered
// by useBulkDeleteToast unit tests. Selection-state tests (F1-F6) never call
// any toast method, so this stub is harmless for them.
vi.mock('@/composables/useBulkDeleteToast', () => ({
  useBulkDeleteToast: () => ({
    showBulkDeleteResult: vi.fn(),
    showValidationError: vi.fn(),
  }),
}))

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

// Phase 107: multi-select + bulk delete UX (Commit 6 RED).
// These tests assume IllustrationGallery exposes a `selection` Set state and
// toggleSelect/clearSelection methods (to be implemented in Commit 10). They
// FAIL in RED state with "toggleSelect is not a function" / similar.
describe('IllustrationGallery (Phase 107: multi-select bulk delete)', () => {
  const sampleAssets = () => [
    { id: 'a', type: 'chapter', chapter_num: 1, style_preset: 'ink', url: '/x' },
    { id: 'b', type: 'chapter', chapter_num: 2, style_preset: 'ink', url: '/y' },
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.$fetch = vi.fn().mockResolvedValue({ assets: [] })
  })

  // F1: selection Set<string> state
  it('F1: toggleSelect adds/removes asset_id from selection Set', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    // Initially empty
    expect(wrapper.vm.selection.size).toBe(0)

    // Toggle 'a' on
    wrapper.vm.toggleSelect('a', true)
    expect(wrapper.vm.selection.has('a')).toBe(true)
    expect(wrapper.vm.selection.size).toBe(1)

    // Toggle 'b' on
    wrapper.vm.toggleSelect('b', true)
    expect(wrapper.vm.selection.size).toBe(2)

    // Toggle 'a' off
    wrapper.vm.toggleSelect('a', false)
    expect(wrapper.vm.selection.has('a')).toBe(false)
    expect(wrapper.vm.selection.size).toBe(1)
  })

  // F2: checkbox overlay renders per card when selectable !== false
  it('F2: checkbox overlay renders per card when selectable !== false', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    const checkboxes = wrapper.findAll('[data-testid^="select-checkbox-"]')
    expect(checkboxes.length).toBe(2)
  })

  // F3: bulk action bar hidden when selection empty, visible when non-empty
  it('F3: bulk action bar hidden when selection empty, visible when non-empty', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    // Initially hidden
    expect(wrapper.find('.bulk-action-bar').exists()).toBe(false)

    // Select one asset
    wrapper.vm.toggleSelect('a', true)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.bulk-action-bar').exists()).toBe(true)
    expect(wrapper.find('.bulk-action-bar__count').text()).toContain('1')

    // Clear
    wrapper.vm.clearSelection()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.bulk-action-bar').exists()).toBe(false)
  })

  // F4: NPopconfirm wraps the bulk-delete button in the bar.
// NPopconfirm (built on NPopover) attaches its click handler to the trigger
// element directly without a wrapper DOM element. The popconfirm panel only
// renders on activation. We verify by clicking the trigger and confirming
// the popconfirm panel content appears (mirrors Phase 106 F1 pattern).
  it('F4: bulk action bar wraps the bulk-delete button in NPopconfirm', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    wrapper.vm.toggleSelect('a', true)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="bulk-delete-btn"]').exists()).toBe(true)

    // Click the trigger button to activate the popconfirm.
    await wrapper.find('[data-testid="bulk-delete-btn"]').trigger('click')
    await wrapper.vm.$nextTick()
    // Popconfirm panel content becomes visible (text + buttons).
    expect(document.body.textContent).toContain('确认删除这')
  })

  // F5: selection persists when store assets are replaced (cross-page simulation)
  it('F5: selection persists when assets prop changes (cross-page simulation)', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    wrapper.vm.toggleSelect('a', true)
    wrapper.vm.toggleSelect('b', true)

    // Simulate page change — store.assets replaced; component-local selection persists
    store.assets = [
      { id: 'c', type: 'chapter', chapter_num: 3, style_preset: 'ink', url: '/c' },
      { id: 'd', type: 'chapter', chapter_num: 4, style_preset: 'ink', url: '/d' },
    ]
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.selection.size).toBe(2)
    expect(wrapper.vm.selection.has('a')).toBe(true)
    expect(wrapper.vm.selection.has('b')).toBe(true)
  })

  // F6: toggling same id twice reduces to single selection; clearSelection resets to 0
  it('F6: toggleSelect on same id twice reduces to single selection', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    wrapper.vm.toggleSelect('a', true)
    wrapper.vm.toggleSelect('a', true)
    expect(wrapper.vm.selection.size).toBe(1)

    wrapper.vm.clearSelection()
    expect(wrapper.vm.selection.size).toBe(0)
  })

  // F7: confirmBulkDelete happy path — store.bulkDeleteAssets called + emit
  // bulk-deleted + selection cleared. The store mutation is the observable
  // surface; toast message rendering is covered by useBulkDeleteToast unit
  // tests (Phase 107), not here (avoid coupling component test to Naive UI's
  // message provider, which requires extra plugin setup).
  it('F7: confirmBulkDelete calls store, emits bulk-deleted, clears selection', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    const bulkSpy = vi.spyOn(store, 'bulkDeleteAssets').mockResolvedValue({
      deleted: ['a'],
      failed: [],
      summary: { total: 1, ok: 1, fail: 0 },
    })

    wrapper.vm.toggleSelect('a', true)
    await wrapper.vm.$nextTick()

    await wrapper.vm.confirmBulkDelete()
    await wrapper.vm.$nextTick()

    // Store was called via the useIllustration wrapper (I1: single access layer).
    expect(bulkSpy).toHaveBeenCalledWith('test-slug', ['a'])
    // bulk-deleted event fired with the API result.
    expect(wrapper.emitted('bulk-deleted')).toBeTruthy()
    expect(wrapper.emitted('bulk-deleted')[0][0]).toEqual({
      deleted: ['a'],
      failed: [],
      summary: { total: 1, ok: 1, fail: 0 },
    })
    // Selection cleared on success.
    expect(wrapper.vm.selection.size).toBe(0)
  })

  // F8: error path — store.bulkDeleteAssets rejects → no emit, selection NOT
  // cleared (so user can retry without re-selecting each asset).
  it('F8: confirmBulkDelete handles store error without emit, keeps selection', async () => {
    const store = useIllustrationStore()
    store.assets = sampleAssets()
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test-slug' } })

    const bulkSpy = vi.spyOn(store, 'bulkDeleteAssets').mockRejectedValue(
      new Error('network down')
    )

    wrapper.vm.toggleSelect('a', true)
    await wrapper.vm.$nextTick()

    await wrapper.vm.confirmBulkDelete()
    await wrapper.vm.$nextTick()

    expect(bulkSpy).toHaveBeenCalledWith('test-slug', ['a'])
    // No bulk-deleted event on error.
    expect(wrapper.emitted('bulk-deleted')).toBeFalsy()
    // Selection preserved so user can retry.
    expect(wrapper.vm.selection.size).toBe(1)
    expect(wrapper.vm.selection.has('a')).toBe(true)
    // Inflight flag reset.
    expect(wrapper.vm.bulkDeleteInFlight).toBe(false)
  })
})