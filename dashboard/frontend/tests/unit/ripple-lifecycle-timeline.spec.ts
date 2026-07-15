// tests/unit/ripple-lifecycle-timeline.spec.ts — Phase 9.50 F39
import { describe, test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RippleLifecycleTimeline from '../../src/components/RippleLifecycleTimeline.vue'
import { buildRippleLifecycleSteps, RIPPLE_LIFECYCLE_STEPS } from '../../src/utils/rippleLifecycleUtils.js'
import { byTestid } from '../helpers/by-testid'

describe('buildRippleLifecycleSteps (Phase 9.50 F39)', () => {
  test('returns 6 steps in canonical order', () => {
    const { steps } = buildRippleLifecycleSteps('pending', [])
    expect(steps.map((s) => s.state)).toEqual([...RIPPLE_LIFECYCLE_STEPS])
  })

  test('pending status marks pending as current and created as completed', () => {
    const { steps, current } = buildRippleLifecycleSteps('pending', [
      { action: 'created' },
    ])
    expect(current).toBe('pending')
    expect(steps.find((s) => s.state === 'created')?.phase).toBe('completed')
    expect(steps.find((s) => s.state === 'pending')?.phase).toBe('current')
    expect(steps.find((s) => s.state === 'confirmed')?.phase).toBe('upcoming')
  })

  test('applied status completes main path through applied', () => {
    const { steps } = buildRippleLifecycleSteps('applied', [
      { action: 'created' },
      { action: 'applied' },
    ])
    expect(steps.find((s) => s.state === 'applied')?.phase).toBe('current')
    expect(steps.find((s) => s.state === 'confirmed')?.phase).toBe('completed')
    expect(steps.find((s) => s.state === 'rejected')?.phase).toBe('upcoming')
  })

  test('rejected status skips applied and highlights rejected', () => {
    const { steps } = buildRippleLifecycleSteps('rejected', [
      { action: 'created' },
      { action: 'rejected' },
    ])
    expect(steps.find((s) => s.state === 'applied')?.phase).toBe('skipped')
    expect(steps.find((s) => s.state === 'rejected')?.phase).toBe('current')
    expect(steps.find((s) => s.state === 'failed')?.phase).toBe('skipped')
  })
})

describe('RippleLifecycleTimeline (Phase 9.50 F39)', () => {
  test('renders 6 lifecycle steps with data-testid', () => {
    const wrapper = mount(RippleLifecycleTimeline, {
      props: { status: 'pending', auditEntries: [{ action: 'created' }] },
    })
    expect(wrapper.get(byTestid('ripple-lifecycle-timeline'))).toBeTruthy()
    for (const state of RIPPLE_LIFECYCLE_STEPS) {
      expect(wrapper.get(byTestid(`lifecycle-step-${state}`))).toBeTruthy()
    }
  })
})
