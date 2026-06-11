// tests/unit/coverage-branches-f48.spec.ts — Phase 9.57 F48 branch boost
import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { buildRippleLifecycleSteps } from '../../src/utils/rippleLifecycleUtils.js'
import { impactNodeColor, IMPACT_DIMENSION_ORDER } from '../../src/utils/impactGraphUtils.js'
import DecisionCard from '../../src/components/DecisionCard.vue'
import { byTestid } from '../helpers/by-testid'

describe('rippleLifecycleUtils branches (F48)', () => {
  test('failed status marks failed current and applied skipped', () => {
    const { steps } = buildRippleLifecycleSteps('failed', [{ action: 'created' }])
    expect(steps.find((s) => s.state === 'failed')?.phase).toBe('current')
    expect(steps.find((s) => s.state === 'applied')?.phase).toBe('skipped')
  })

  test('confirmed status completes through confirmed', () => {
    const { steps } = buildRippleLifecycleSteps('confirmed', [{ action: 'created' }])
    expect(steps.find((s) => s.state === 'confirmed')?.phase).toBe('current')
    expect(steps.find((s) => s.state === 'pending')?.phase).toBe('completed')
  })

  test('unknown status yields null current', () => {
    const { current } = buildRippleLifecycleSteps('bogus', [])
    expect(current).toBeNull()
  })

  test('audit entries without action still mark created completed', () => {
    const { steps } = buildRippleLifecycleSteps('pending', [{}])
    expect(steps.find((s) => s.state === 'created')?.phase).toBe('completed')
  })
})

describe('impactGraphUtils (F48)', () => {
  test('known dimension colors', () => {
    expect(impactNodeColor('character')).toBe('#3b82f6')
    expect(impactNodeColor('unknown_dim')).toBe('#9ca3af')
  })

  test('dimension order stable', () => {
    expect(IMPACT_DIMENSION_ORDER).toHaveLength(4)
  })
})

describe('DecisionCard branches (F48)', () => {
  const base = {
    decision_id: 'd1',
    node_id: 'n1',
    kind: 'outline-judgment',
    prompt: 'Choose',
    options: ['A', 'B'],
    status: 'pending',
    priority: 2,
  }

  test('pending shows option and action buttons', () => {
    const wrapper = mount(DecisionCard, { props: { decision: base } })
    expect(wrapper.findAll(byTestid('option-btn')).length).toBe(2)
    expect(wrapper.find(byTestid('defer-btn')).exists()).toBe(true)
  })

  test('resolved shows readonly hint and meta', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          ...base,
          status: 'resolved',
          resolved_by: 'alice',
          resolution: 'A',
          resolved_at: '2026-06-11T12:00:00Z',
        },
      },
    })
    expect(wrapper.find(byTestid('readonly-hint')).text()).toContain('解决')
    expect(wrapper.find(byTestid('meta-info')).exists()).toBe(true)
  })

  test('cancelled shows cancel readonly hint', () => {
    const wrapper = mount(DecisionCard, {
      props: { decision: { ...base, status: 'cancelled', reason: 'later' } },
    })
    expect(wrapper.find(byTestid('readonly-hint')).text()).toContain('取消')
  })

  test('deferred shows defer readonly hint', () => {
    const wrapper = mount(DecisionCard, {
      props: { decision: { ...base, status: 'deferred', reason: 'busy' } },
    })
    expect(wrapper.find(byTestid('readonly-hint')).text()).toContain('推迟')
  })

  test('context details render when present', () => {
    const wrapper = mount(DecisionCard, {
      props: { decision: { ...base, context: { chapter: 3 } } },
    })
    expect(wrapper.find('details').exists()).toBe(true)
  })

  test('emits resolve on option click', async () => {
    const wrapper = mount(DecisionCard, { props: { decision: base } })
    await wrapper.findAll(byTestid('option-btn'))[0].trigger('click')
    expect(wrapper.emitted('resolve')?.[0]?.[0]).toEqual({ decisionId: 'd1', option: 'A' })
  })

  test('defer and cancel emit with prompt/confirm', async () => {
    vi.stubGlobal('prompt', vi.fn().mockReturnValue('later'))
    vi.stubGlobal('confirm', vi.fn().mockReturnValue(true))
    const wrapper = mount(DecisionCard, { props: { decision: base } })
    await wrapper.find(byTestid('defer-btn')).trigger('click')
    expect(wrapper.emitted('defer')?.[0]?.[0]).toEqual({ decisionId: 'd1', reason: 'later' })
    await wrapper.find(byTestid('cancel-btn')).trigger('click')
    expect(wrapper.emitted('cancel')?.[0]?.[0]).toEqual({ decisionId: 'd1', reason: 'later' })
    vi.unstubAllGlobals()
  })

  test('cancel confirm false does not emit', async () => {
    vi.stubGlobal('confirm', vi.fn().mockReturnValue(false))
    const wrapper = mount(DecisionCard, { props: { decision: base } })
    await wrapper.find(byTestid('cancel-btn')).trigger('click')
    expect(wrapper.emitted('cancel')).toBeUndefined()
    vi.unstubAllGlobals()
  })
})
