// tests/unit/decision-card-meta-info.spec.ts — Phase 9.52 F41
// DecisionCard meta-info 4 sub-element testid: resolved_by / resolution / resolved_at / reason

import { describe, test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DecisionCard from '../../src/components/DecisionCard.vue'
import { byTestid } from '../helpers/by-testid'

const baseResolved = {
  decision_id: 'd-meta',
  status: 'resolved' as const,
  kind: 'outline_judgment',
  prompt: '审核',
  options: [],
  resolved_by: '主公',
  resolution: '选项 A',
  resolved_at: '2026-06-08T10:00:00',
  reason: 'OK',
}

describe('DecisionCard meta-info sub-element testid (Phase 9.52 F41)', () => {
  test('meta-resolved-by testid renders resolver name', () => {
    const wrapper = mount(DecisionCard, { props: { decision: baseResolved } })
    const el = wrapper.find(byTestid('meta-resolved-by'))
    expect(el.exists()).toBe(true)
    expect(el.text()).toContain('主公')
  })

  test('meta-resolution testid renders chosen option', () => {
    const wrapper = mount(DecisionCard, { props: { decision: baseResolved } })
    const el = wrapper.find(byTestid('meta-resolution'))
    expect(el.exists()).toBe(true)
    expect(el.text()).toContain('选项 A')
  })

  test('meta-resolved-at testid renders formatted timestamp', () => {
    const wrapper = mount(DecisionCard, { props: { decision: baseResolved } })
    const el = wrapper.find(byTestid('meta-resolved-at'))
    expect(el.exists()).toBe(true)
    expect(el.text()).toContain('时间:')
  })

  test('meta-reason testid uses 取消原因 label for cancelled status', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          ...baseResolved,
          status: 'cancelled',
          resolution: undefined,
          reason: '实验失败',
        },
      },
    })
    const el = wrapper.find(byTestid('meta-reason'))
    expect(el.exists()).toBe(true)
    expect(el.text()).toContain('取消原因')
    expect(el.text()).toContain('实验失败')
  })
})
