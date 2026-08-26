// tests/unit/pages/world-page.spec.ts — Task 12 (Task F)
// WorldPage skeleton + WorldTabs coverage smoke test.
// Exercises: page testid mount + 4 tab testids render.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import WorldPage from '../../../src/pages/WorldPage.vue'

vi.mock('../../../src/composables/world/useWorldDb', () => ({
  useWorldDb: () => ({
    listCharacters: vi.fn().mockResolvedValue([]),
    listFactions: vi.fn().mockResolvedValue([]),
    listLore: vi.fn().mockResolvedValue([]),
    listTimeline: vi.fn().mockResolvedValue([]),
    listRelationships: vi.fn().mockResolvedValue([]),
  }),
}))

vi.mock('../../../src/composables/world/useWorldReview', () => ({
  useWorldReview: () => ({
    listProposals: vi.fn().mockResolvedValue([]),
  }),
}))

describe('WorldPage (Task F)', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  test('renders page testid', async () => {
    const w = mount(WorldPage)
    await flushPromises()
    expect(w.find('[data-testid="world-page"]').exists()).toBe(true)
  })

  test('renders 4 tabs', async () => {
    const w = mount(WorldPage)
    await flushPromises()
    expect(w.find('[data-testid="world-tab-characters"]').exists()).toBe(true)
    expect(w.find('[data-testid="world-tab-factions"]').exists()).toBe(true)
    expect(w.find('[data-testid="world-tab-timeline"]').exists()).toBe(true)
    expect(w.find('[data-testid="world-tab-lore"]').exists()).toBe(true)
  })
})