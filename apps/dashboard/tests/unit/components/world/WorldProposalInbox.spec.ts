import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

// Helper: mount and open the proposal inbox panel so the extract section is visible.
async function mountAndOpen() {
  const wrapper = mount(WorldProposalInbox)
  await flushPromises()
  await wrapper.find('[data-testid="proposal-inbox-toggle"]').trigger('click')
  await flushPromises()
  return wrapper
}

// Stub composables used by WorldProposalInbox
const listProposalsMock = vi.fn()
const acceptProposalMock = vi.fn()
const rejectProposalMock = vi.fn()
const listCharactersMock = vi.fn()
const fetchChapterTextsMock = vi.fn()
const extractFromChaptersMock = vi.fn()

vi.mock('@/composables/world/useWorldReview.js', () => ({
  useWorldReview: () => ({
    listProposals: listProposalsMock,
    acceptProposal: acceptProposalMock,
    rejectProposal: rejectProposalMock,
  }),
}))

vi.mock('@/composables/world/useWorldDb.js', () => ({
  useWorldDb: () => ({
    listCharacters: listCharactersMock,
  }),
}))

vi.mock('@/composables/world/useWorldAgent.js', () => ({
  useWorldAgent: () => ({
    fetchChapterTexts: fetchChapterTextsMock,
    extractFromChapters: extractFromChaptersMock,
  }),
}))

import WorldProposalInbox from '@/components/world/WorldProposalInbox.vue'

const mockCharacters = [
  { id: 1, slug: 'lu-chen', name: '陆沉' },
  { id: 2, slug: 'gu-yao', name: '顾遥' },
]

describe('WorldProposalInbox — extract section', () => {
  beforeEach(() => {
    listProposalsMock.mockReset()
    listProposalsMock.mockResolvedValue([])
    listCharactersMock.mockReset()
    listCharactersMock.mockResolvedValue(mockCharacters)
    fetchChapterTextsMock.mockReset()
    extractFromChaptersMock.mockReset()
    extractFromChaptersMock.mockResolvedValue({
      proposals_created: 0,
      ids: [],
      message: 'extracted 0 proposal(s) from chapters 1-5',
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders extract section with placeholder option initially', async () => {
    const wrapper = await mountAndOpen()
    const select = wrapper.find('[data-testid="world-proposal-inbox-extract-slug"]')
    expect(select.exists()).toBe(true)
    const options = select.findAll('option')
    // placeholder + 2 characters
    expect(options.length).toBe(3)
    expect(options[0].text()).toBe('请选择')
  })

  it('populates character dropdown from listCharacters', async () => {
    const wrapper = await mountAndOpen()
    const select = wrapper.find('[data-testid="world-proposal-inbox-extract-slug"]')
    const options = select.findAll('option')
    expect(options[1].attributes('value')).toBe('lu-chen')
    expect(options[2].attributes('value')).toBe('gu-yao')
  })

  it('disables extract button when no character selected', async () => {
    const wrapper = await mountAndOpen()
    const btn = wrapper.find('[data-testid="world-proposal-inbox-extract-button"]')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('clicking extract calls fetchChapterTexts then extractFromChapters with chapter texts', async () => {
    fetchChapterTextsMock.mockResolvedValue({
      texts: ['body1', 'body2'],
      found: 2,
      requested: 2,
    })
    extractFromChaptersMock.mockResolvedValue({
      proposals_created: 2,
      ids: [10, 11],
      message: 'extracted 2 proposal(s) from chapters 1-2',
    })

    const wrapper = await mountAndOpen()

    const select = wrapper.find('[data-testid="world-proposal-inbox-extract-slug"]')
    await select.setValue('lu-chen')
    await wrapper.find('[data-testid="world-proposal-inbox-extract-start"]').setValue('1')
    await wrapper.find('[data-testid="world-proposal-inbox-extract-end"]').setValue('2')

    await wrapper.find('[data-testid="world-proposal-inbox-extract-button"]').trigger('click')
    await flushPromises()

    expect(fetchChapterTextsMock).toHaveBeenCalledWith(
      'lingwen-novel',
      expect.objectContaining({ start: 1, end: 2 }),
    )
    expect(extractFromChaptersMock).toHaveBeenCalledWith(
      'lu-chen',
      expect.objectContaining({ start: 1, end: 2 }),
      ['body1', 'body2'],
    )
  })

  it('displays extract result message after success', async () => {
    fetchChapterTextsMock.mockResolvedValue({
      texts: ['b1'],
      found: 1,
      requested: 1,
    })
    extractFromChaptersMock.mockResolvedValue({
      proposals_created: 1,
      ids: [42],
      message: 'extracted 1 proposal(s) from chapters 1-1',
    })

    const wrapper = await mountAndOpen()

    await wrapper.find('[data-testid="world-proposal-inbox-extract-slug"]').setValue('gu-yao')
    await wrapper.find('[data-testid="world-proposal-inbox-extract-start"]').setValue('1')
    await wrapper.find('[data-testid="world-proposal-inbox-extract-end"]').setValue('1')

    await wrapper.find('[data-testid="world-proposal-inbox-extract-button"]').trigger('click')
    await flushPromises()

    const result = wrapper.find('[data-testid="world-proposal-inbox-extract-result"]')
    expect(result.exists()).toBe(true)
    expect(result.text()).toContain('extracted 1 proposal(s) from chapters 1-1')
  })
})