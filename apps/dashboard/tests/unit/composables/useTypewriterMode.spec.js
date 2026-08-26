import { describe, it, expect } from 'vitest'
import { useTypewriterMode } from '@/composables/useTypewriterMode'

describe('useTypewriterMode', () => {
  it('starts enabled=false', () => {
    const tm = useTypewriterMode()
    expect(tm.enabled.value).toBe(false)
  })

  it('toggle flips value', () => {
    const tm = useTypewriterMode()
    tm.toggle()
    expect(tm.enabled.value).toBe(true)
    tm.toggle()
    expect(tm.enabled.value).toBe(false)
  })

  it('computeOffset returns 0 when disabled', () => {
    const tm = useTypewriterMode()
    expect(tm.computeOffset(100)).toBe(0)
  })

  it('computeOffset returns scrollTarget - 1/3 viewport when enabled', () => {
    const tm = useTypewriterMode()
    tm.toggle()
    const offset = tm.computeOffset(300, 600)
    expect(offset).toBe(100) // 300 - 600/3 = 300 - 200 = 100
  })
})
