// Phase 108: bulk regenerate button + handler in IllustrationGallery.vue.
// Mirrors Phase 107 F1-F6 (bulk delete) pattern + adds F7/F8 end-to-end tests
// (3 selected → API called → toast + emit + clear / API throws → toast error → retain).
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { NPopconfirm } from 'naive-ui'
import { ref } from 'vue'
import IllustrationGallery from './IllustrationGallery.vue'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Shared mock state (module-level so vi.mock factory returns same refs across
// invocations during the test run — Vue templates read these refs reactively).
const mockAssets = ref([])
const mockError = ref(null)
const mockLoadAssets = vi.fn()
const mockRegenerate = vi.fn()
const mockDeleteAsset = vi.fn()
const mockBulkDeleteAssets = vi.fn()
const mockBulkRegenerateAssets = vi.fn()

vi.mock('@/composables/useIllustration', () => ({
  useIllustration: () => ({
    assets: mockAssets,
    error: mockError,
    loadAssets: mockLoadAssets,
    regenerate: mockRegenerate,
    deleteAsset: mockDeleteAsset,
    bulkDeleteAssets: mockBulkDeleteAssets,
    // Phase 108: bulkRegenerateAssets wired through useIllustration (Task B8).
    // Signature: (slug, assetIds, opts) => Promise<BulkRegenerateResult>.
    bulkRegenerateAssets: mockBulkRegenerateAssets,
  }),
}))

const mockBulkDeleteToast = {
  showBulkDeleteResult: vi.fn(),
  showValidationError: vi.fn(),
}
const mockBulkRegenerateToast = {
  showResult: vi.fn(),
  showValidationError: vi.fn(),
  showNetworkError: vi.fn(),
}

vi.mock('@/composables/useBulkDeleteToast', () => ({
  useBulkDeleteToast: () => mockBulkDeleteToast,
}))
vi.mock('@/composables/useBulkRegenerateToast', () => ({
  useBulkRegenerateToast: () => mockBulkRegenerateToast,
}))

// Stub IllustrationCard to keep tests focused on bulk-regenerate logic — we
// don't need to verify card rendering for these tests.
vi.mock('./IllustrationCard.vue', () => ({
  default: {
    name: 'IllustrationCard',
    template: '<div class="illustration-card-stub" :data-asset-id="asset.id" />',
    props: ['asset'],
    emits: ['regenerate', 'delete'],
  },
}))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Find the NPopconfirm component that wraps the bulk-regenerate button.
 * NPopconfirm uses a Teleport for its popper, so `pc.$el` may be undefined.
 * Scoping to the bulk action bar (which only contains the 2 bulk NPopconfirms)
 * avoids per-card NPopconfirms from IllustrationCard. Identifies the regenerate
 * NPopconfirm by checking which one contains the regenerate button in its trigger.
 */
function findRegeneratePopconfirm(wrapper) {
  const bulkBar = wrapper.find('[data-testid="bulk-action-bar"]')
  const popconfirmsInBar = bulkBar.findAllComponents(NPopconfirm)
  for (const pc of popconfirmsInBar) {
    const triggerEl = pc.find('[data-testid="bulk-regenerate-btn"]')
    if (triggerEl.exists()) return pc
  }
  return null
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('IllustrationGallery — bulk regenerate (Phase 108)', () => {
  beforeEach(() => {
    mockAssets.value = [
      { id: 'a', type: 'chapter', chapter_num: 1, url: '/a', style_preset: 'ink', scene_json: { old: 'a' } },
      { id: 'b', type: 'chapter', chapter_num: 1, url: '/b', style_preset: 'ink', scene_json: { old: 'b' } },
      { id: 'c', type: 'chapter', chapter_num: 1, url: '/c', style_preset: 'ink', scene_json: { old: 'c' } },
    ]
    mockError.value = null
    mockLoadAssets.mockReset()
    mockRegenerate.mockReset()
    mockDeleteAsset.mockReset()
    mockBulkDeleteAssets.mockReset()
    mockBulkRegenerateAssets.mockReset()
    mockBulkDeleteToast.showBulkDeleteResult.mockReset()
    mockBulkDeleteToast.showValidationError.mockReset()
    mockBulkRegenerateToast.showResult.mockReset()
    mockBulkRegenerateToast.showValidationError.mockReset()
    mockBulkRegenerateToast.showNetworkError.mockReset()
  })

  it('F1: bulk-regenerate button hidden when selection empty', () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    // Bulk action bar itself is hidden when selection.size === 0, so the
    // regenerate button inside it is also hidden.
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="bulk-regenerate-btn"]').exists()).toBe(false)
  })

  it('F2: bulk-regenerate button visible after selection >= 1', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    wrapper.vm.toggleSelect('a', true)
    await flushPromises()
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="bulk-regenerate-btn"]').exists()).toBe(true)
  })

  it('F3: bulk-regenerate button wrapped in NPopconfirm', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    wrapper.vm.toggleSelect('a', true)
    await flushPromises()

    const regenBtn = wrapper.find('[data-testid="bulk-regenerate-btn"]')
    expect(regenBtn.exists()).toBe(true)
    // The button must be the trigger of an NPopconfirm so the user can
    // confirm before running the (potentially slow) bulk regenerate.
    const popconfirm = findRegeneratePopconfirm(wrapper)
    expect(popconfirm).not.toBeNull()
  })

  it('F4: NPopconfirm positive-click triggers store.bulkRegenerateAssets', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    wrapper.vm.toggleSelect('a', true)
    await flushPromises()

    mockBulkRegenerateAssets.mockResolvedValueOnce({
      regenerated: [{ id: 'a', url: '/new-a', scene_json: { new: 'a' } }],
      failed: [],
      summary: { total: 1, ok: 1, fail: 0 },
    })

    const popconfirm = findRegeneratePopconfirm(wrapper)
    popconfirm.vm.$emit('positive-click')
    await flushPromises()

    expect(mockBulkRegenerateAssets).toHaveBeenCalledTimes(1)
    expect(mockBulkRegenerateAssets).toHaveBeenCalledWith('demo', ['a'])
  })

  it('F5: selection cleared on success', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    wrapper.vm.toggleSelect('a', true)
    wrapper.vm.toggleSelect('b', true)
    await flushPromises()
    // Selection size verified via DOM (script setup refs aren't on wrapper.vm).
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="bulk-action-bar"]').text()).toContain('已选 2')

    mockBulkRegenerateAssets.mockResolvedValueOnce({
      regenerated: [{ id: 'a' }, { id: 'b' }],
      failed: [],
      summary: { total: 2, ok: 2, fail: 0 },
    })

    const popconfirm = findRegeneratePopconfirm(wrapper)
    popconfirm.vm.$emit('positive-click')
    await flushPromises()

    // Bulk action bar disappears when selection is cleared.
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(false)
  })

  it('F6: emits "bulk-regenerated" with result on success', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    wrapper.vm.toggleSelect('a', true)
    await flushPromises()

    const result = {
      regenerated: [{ id: 'a', url: '/new-a' }],
      failed: [],
      summary: { total: 1, ok: 1, fail: 0 },
    }
    mockBulkRegenerateAssets.mockResolvedValueOnce(result)

    const popconfirm = findRegeneratePopconfirm(wrapper)
    popconfirm.vm.$emit('positive-click')
    await flushPromises()

    const events = wrapper.emitted('bulk-regenerated')
    expect(events).toBeTruthy()
    expect(events).toHaveLength(1)
    expect(events[0][0]).toEqual(result)
  })

  it('F7: end-to-end happy path — 3 selected → API called → toast success → emit + selection cleared', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    wrapper.vm.toggleSelect('a', true)
    wrapper.vm.toggleSelect('b', true)
    wrapper.vm.toggleSelect('c', true)
    await flushPromises()

    const result = {
      regenerated: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
      failed: [],
      summary: { total: 3, ok: 3, fail: 0 },
    }
    mockBulkRegenerateAssets.mockResolvedValueOnce(result)

    const popconfirm = findRegeneratePopconfirm(wrapper)
    popconfirm.vm.$emit('positive-click')
    await flushPromises()

    // API called once with all 3 ids (order preserved: Set → Array.from).
    expect(mockBulkRegenerateAssets).toHaveBeenCalledWith('demo', ['a', 'b', 'c'])
    // Toast rendered success variant (full success → showResult path).
    expect(mockBulkRegenerateToast.showResult).toHaveBeenCalledWith(result)
    // Component emitted bulk-regenerated with the API result.
    expect(wrapper.emitted('bulk-regenerated')).toBeTruthy()
    expect(wrapper.emitted('bulk-regenerated')[0][0]).toEqual(result)
    // Selection cleared so the user can pick again — bulk action bar hidden.
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(false)
  })

  it('F8: end-to-end error path — API throws → toast error → selection retained', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo' } })
    wrapper.vm.toggleSelect('a', true)
    wrapper.vm.toggleSelect('b', true)
    await flushPromises()

    mockBulkRegenerateAssets.mockRejectedValueOnce(new Error('bulk regenerate failed: 500'))

    const popconfirm = findRegeneratePopconfirm(wrapper)
    popconfirm.vm.$emit('positive-click')
    await flushPromises()

    // showValidationError surfaces the API error message; showResult is NOT called.
    expect(mockBulkRegenerateToast.showValidationError).toHaveBeenCalledTimes(1)
    expect(mockBulkRegenerateToast.showValidationError).toHaveBeenCalledWith('bulk regenerate failed: 500')
    expect(mockBulkRegenerateToast.showResult).not.toHaveBeenCalled()
    // No emit because the path didn't succeed.
    expect(wrapper.emitted('bulk-regenerated')).toBeFalsy()
    // Selection retained so the user can retry without re-selecting — bulk
    // action bar still visible because selection.size > 0.
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="bulk-action-bar"]').text()).toContain('已选 2')
  })
})