// tests/unit/decision-card-status.spec.ts — Phase 8.45.1
// DecisionCard 3 status testid: status-resolved / status-deferred / status-cancelled
// 跟 Phase 8.38 kind testid `decision-kind-${kindClass}` 1:1 mirror pattern.
// 跟 Phase 8.32 L16 generic `data-testid="status-badge"` 互不冲突 (specific +
// generic 2 个 testid attribute 同 span).
//
// Phase 8.32 已加 generic status-badge + 6 inner testid. Phase 8.45.1 收尾 specific
// 3 status testid (mirror 3 class names: status-resolved/-deferred/-cancelled), e2e
// 找特定 status 节点得 `.find('.status-resolved')` 脆 selector, 改 byTestid 稳定
// selector.

import { describe, test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'
import DecisionCard from '../../src/components/DecisionCard.vue'

describe('DecisionCard 3 status testid (Phase 8.45.1)', () => {
  test('resolved status → status-resolved testid renders + 1:1 镜像 class', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          decision_id: 'd1',
          kind: 'outline_judgment',
          status: 'resolved',
          prompt: '...',
          options: [],
        },
      },
    })
    // resolved: status-resolved testid 在位 + 镜像 class
    const el = wrapper.find(byTestid('status-resolved'))
    expect(el.exists()).toBe(true)
    expect(el.classes()).toContain('status-resolved')
    // 其他 2 status testid 不在
    expect(wrapper.find(byTestid('status-deferred')).exists()).toBe(false)
    expect(wrapper.find(byTestid('status-cancelled')).exists()).toBe(false)
  })

  test('deferred status → status-deferred testid renders + 1:1 镜像 class', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          decision_id: 'd2',
          kind: 'volume_judgment',
          status: 'deferred',
          prompt: '...',
          options: [],
        },
      },
    })
    const el = wrapper.find(byTestid('status-deferred'))
    expect(el.exists()).toBe(true)
    expect(el.classes()).toContain('status-deferred')
    expect(wrapper.find(byTestid('status-resolved')).exists()).toBe(false)
    expect(wrapper.find(byTestid('status-cancelled')).exists()).toBe(false)
  })

  test('cancelled status → status-cancelled testid renders + 1:1 镜像 class', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          decision_id: 'd3',
          kind: 'chapter_iteration_judgment',
          status: 'cancelled',
          prompt: '...',
          options: [],
        },
      },
    })
    const el = wrapper.find(byTestid('status-cancelled'))
    expect(el.exists()).toBe(true)
    expect(el.classes()).toContain('status-cancelled')
    expect(wrapper.find(byTestid('status-resolved')).exists()).toBe(false)
    expect(wrapper.find(byTestid('status-deferred')).exists()).toBe(false)
  })

  test('pending status → 0 status testid (statusBadge map 不含 pending, v-if absent)', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          decision_id: 'd4',
          kind: 'outline_judgment',
          status: 'pending',
          prompt: '...',
          options: ['A', 'B'],
        },
      },
    })
    // pending: 0 specific status testid + 0 generic status-badge (Phase 8.32 验证)
    expect(wrapper.find(byTestid('status-resolved')).exists()).toBe(false)
    expect(wrapper.find(byTestid('status-deferred')).exists()).toBe(false)
    expect(wrapper.find(byTestid('status-cancelled')).exists()).toBe(false)
    expect(wrapper.findAll(byTestid('status-badge'))).toHaveLength(0)
  })
})
