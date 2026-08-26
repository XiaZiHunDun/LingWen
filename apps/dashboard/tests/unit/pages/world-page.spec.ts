// tests/unit/pages/world-page.spec.ts — Task 12 (Task F) + Task 13
// WorldPage skeleton + WorldTabs coverage smoke test.
// Exercises: page testid mount + 4 tab testids render.
// Task 13 extends with CharacterList cards test.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import WorldPage from '../../../src/pages/WorldPage.vue'
import { byTestid } from '../../helpers/by-testid'

const listCharactersMock = vi.fn().mockResolvedValue([])
const listFactionsMock = vi.fn().mockResolvedValue([])
const listLoreMock = vi.fn().mockResolvedValue([])
const listTimelineMock = vi.fn().mockResolvedValue([])
const listRelationshipsMock = vi.fn().mockResolvedValue([])

vi.mock('../../../src/composables/world/useWorldDb', () => ({
  useWorldDb: () => ({
    listCharacters: listCharactersMock,
    listFactions: listFactionsMock,
    listLore: listLoreMock,
    listTimeline: listTimelineMock,
    listRelationships: listRelationshipsMock,
  }),
}))

vi.mock('../../../src/composables/world/useWorldReview', () => ({
  useWorldReview: () => ({
    listProposals: vi.fn().mockResolvedValue([]),
  }),
}))

describe('WorldPage (Task F)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    listCharactersMock.mockReset()
    listCharactersMock.mockResolvedValue([])
  })

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

describe('WorldPage (Task 13 — CharacterList cards)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    listCharactersMock.mockReset()
    listCharactersMock.mockResolvedValue([
      { id: 1, slug: 'a', name: 'A', canon_level: 'Draft' },
      { id: 2, slug: 'b', name: 'B', canon_level: 'Established' },
    ])
  })

  test('CharacterList shows cards from API', async () => {
    const w = mount(WorldPage)
    await flushPromises()
    expect(w.find(byTestid('character-card-a')).exists()).toBe(true)
    expect(w.find(byTestid('character-card-b')).exists()).toBe(true)
  })
})