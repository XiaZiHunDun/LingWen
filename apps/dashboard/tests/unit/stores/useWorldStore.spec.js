import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWorldStore } from '@/stores/useWorldStore'

describe('useWorldStore', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('starts on characters tab', () => {
    const s = useWorldStore()
    expect(s.activeTab).toBe('characters')
  })

  it('switchTab updates activeTab', () => {
    const s = useWorldStore()
    s.switchTab('factions')
    expect(s.activeTab).toBe('factions')
  })

  it('sets filters', () => {
    const s = useWorldStore()
    s.setCanonLevelFilter('Draft')
    expect(s.canonLevelFilter).toBe('Draft')
  })
})