import { describe, it, expect, vi, beforeEach } from 'vitest'

// The composable fetches via @/api/studio.fetchStudioProjects; mock it.
import { useBootState } from '@/composables/useBootState'

describe('useBootState', () => {
  beforeEach(() => vi.resetModules())

  it('marks noProject=true when /studio/projects returns an empty list', async () => {
    vi.doMock('@/api/studio', () => ({
      fetchStudioProjects: () => Promise.resolve({ projects: [], active_slug: null }),
    }))
    const { useBootState: boot } = await import('@/composables/useBootState')
    const state = boot()
    await state.check()
    expect(state.noProject.value).toBe(true)
    expect(state.error.value).toBeNull()
    expect(state.booting.value).toBe(false)
  })

  it('marks noProject=true when /studio/projects returns 404 (no project configured)', async () => {
    vi.doMock('@/api/studio', () => ({
      fetchStudioProjects: () => {
        const e = new Error('no studio projects configured')
        e.status = 404
        return Promise.reject(e)
      },
    }))
    const { useBootState: boot } = await import('@/composables/useBootState')
    const state = boot()
    await state.check()
    expect(state.noProject.value).toBe(true)
  })

  it('marks noProject=false when projects exist', async () => {
    vi.doMock('@/api/studio', () => ({
      fetchStudioProjects: () => Promise.resolve({ projects: [{ slug: 'a' }], active_slug: 'a' }),
    }))
    const { useBootState: boot } = await import('@/composables/useBootState')
    const state = boot()
    await state.check()
    expect(state.noProject.value).toBe(false)
  })

  it('records error (not noProject) for non-404 failures, and refresh re-checks', async () => {
    const failures = [new Error('backend down')]
    vi.doMock('@/api/studio', () => ({
      fetchStudioProjects: () =>
        failures.length
          ? Promise.reject(failures.shift())
          : Promise.resolve({ projects: [{ slug: 'a' }], active_slug: 'a' }),
    }))
    const { useBootState: boot } = await import('@/composables/useBootState')
    const state = boot()
    await state.check()
    expect(state.noProject.value).toBe(false)
    expect(state.error.value).toBe('backend down')

    await state.refresh()
    expect(state.noProject.value).toBe(false)
    expect(state.error.value).toBeNull()
  })
})