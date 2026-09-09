// tests/unit/use-pilot-batch-preflight.spec.ts — Phase 41
// runPreflight: populates preflightRows from studioProductionPreflight response.

import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/studio', () => ({
  studioProductionPreflight: vi.fn(),
}))

import { studioProductionPreflight } from '@/api/studio'
import { usePilotBatch } from '@/composables/usePilotBatch'

const mockPreflight = vi.mocked(studioProductionPreflight)

const mockResponse = {
  slug: 'demo',
  mode: 'canon',
  start_chapter: 1,
  end_chapter: 2,
  all_ok: false,
  chapters: [
    { chapter: 1, ok: true, message: 'ok' },
    { chapter: 2, ok: false, message: 'missing characters' },
  ],
  batch_command: 'echo hello',
}

describe('usePilotBatch.runPreflight', () => {
  beforeEach(() => {
    mockPreflight.mockReset()
  })

  test('populates preflightRows from backend chapters on success', async () => {
    mockPreflight.mockResolvedValue(mockResponse)

    const pilot = usePilotBatch()
    await pilot.runPreflight({ slug: 'demo', start_chapter: 1, end_chapter: 2 })

    expect(pilot.preflightRows.value).toEqual([
      { chapter: 1, ok: true, message: 'ok' },
      { chapter: 2, ok: false, message: 'missing characters' },
    ])
    expect(pilot.preflightLoading.value).toBe(false)
    expect(pilot.preflightError.value).toBeNull()
  })

  test('passes start/end chapter (not slug) to studioProductionPreflight', async () => {
    mockPreflight.mockResolvedValue(mockResponse)

    const pilot = usePilotBatch()
    await pilot.runPreflight({ slug: 'demo', start_chapter: 5, end_chapter: 8 })

    expect(mockPreflight).toHaveBeenCalledWith({
      start_chapter: 5,
      end_chapter: 8,
    })
  })

  test('captures error message in preflightError on failure', async () => {
    mockPreflight.mockRejectedValue(new Error('network down'))

    const pilot = usePilotBatch()
    await pilot.runPreflight({ slug: 'demo', start_chapter: 1, end_chapter: 1 }).catch(() => {})

    expect(pilot.preflightError.value).toBe('network down')
    expect(pilot.preflightLoading.value).toBe(false)
  })
})