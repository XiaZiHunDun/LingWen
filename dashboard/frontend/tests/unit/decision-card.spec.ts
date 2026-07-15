// tests/unit/decision-card.spec.ts — Phase 8.32
// DecisionCard 3 status 状态 (pending/resolved/cancelled) inner testid 验证.
// 跟 Phase 6.6.B 注释设计一致: statusBadge map 含 resolved/deferred/cancelled 3
// key (都显), readonly-hint 走 v-else L59 (non-pending 都显), meta-info 3 status
// 都会渲染 (pending 返 null). Spec 抓住这个语义边界 (resolved/cancelled 的
// statusBadge class + text 不同 + readonly-hint 文字不同).

import { describe, test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DecisionCard from '../../src/components/DecisionCard.vue'
import { byTestid } from '../helpers/by-testid'

interface Decision {
  decision_id: string
  status: 'pending' | 'resolved' | 'deferred' | 'cancelled'
  kind?: string
  priority?: number
  prompt?: string
  options?: string[]
  context?: Record<string, unknown>
  resolved_by?: string
  resolution?: string
  resolved_at?: string
  reason?: string
}

describe('DecisionCard inner sub-element testid (Phase 8.32)', () => {
  test('pending decision renders options + defer + cancel, no status-badge, no readonly-hint, no meta-info', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          decision_id: 'd1',
          status: 'pending',
          kind: 'outline_judgment',
          priority: 1,
          options: ['选项 A', '选项 B', '选项 C'],
          prompt: '请审核大纲',
          context: {},
        } as Decision,
      },
    })

    // pending: 3 个 option 按钮 + defer + cancel 显
    expect(wrapper.findAll(byTestid('option-btn'))).toHaveLength(3)
    expect(wrapper.find(byTestid('defer-btn')).exists()).toBe(true)
    expect(wrapper.find(byTestid('cancel-btn')).exists()).toBe(true)
    // pending: 0 specific status testid (statusBadge map 不含 pending, v-if absent) + readonly-hint 0 (v-else 不触发) + meta-info 0 (metaInfo computed 返 null)
    // 注: Phase 8.45.1 drop Phase 8.32 加的 generic `data-testid="status-badge"`, 改 dynamic-only pattern, `status-badge` testid 全 .vue 不再存在 (vacuous 0)
    expect(wrapper.findAll(byTestid('status-badge'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('status-resolved'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('status-deferred'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('status-cancelled'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('readonly-hint'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('meta-info'))).toHaveLength(0)
  })

  test('resolved decision renders status-badge (status-resolved) + readonly-hint (解决) + meta-info, no buttons', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          decision_id: 'd2',
          status: 'resolved',
          options: ['选项 A', '选项 B'],
          resolved_by: '主公',
          resolution: '选项 A',
          resolved_at: '2026-06-08T10:00:00',
          reason: 'OK',
        } as Decision,
      },
    })

    // resolved: 无 button (pending 才渲染)
    expect(wrapper.findAll(byTestid('option-btn'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('defer-btn'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('cancel-btn'))).toHaveLength(0)
    // resolved: status-badge 1 (含 status-resolved class) + readonly-hint 1
    // (走 v-else L59 + 三元 fallback 'resolved' ? '解决' : ...) + meta-info 1
    const statusBadge = wrapper.find(byTestid('status-resolved'))
    expect(statusBadge.exists()).toBe(true)
    expect(statusBadge.classes()).toContain('status-resolved')
    const readonlyHint = wrapper.find(byTestid('readonly-hint'))
    expect(readonlyHint.exists()).toBe(true)
    expect(readonlyHint.text()).toContain('解决')
    const metaInfo = wrapper.find(byTestid('meta-info'))
    expect(metaInfo.exists()).toBe(true)
    expect(metaInfo.text()).toContain('解决人')
    expect(metaInfo.text()).toContain('选项 A')
    expect(metaInfo.text()).toContain('时间')
  })

  test('cancelled decision renders status-badge (status-cancelled) + readonly-hint (取消) + meta-info, no buttons', () => {
    const wrapper = mount(DecisionCard, {
      props: {
        decision: {
          decision_id: 'd3',
          status: 'cancelled',
          resolved_by: '主公',
          resolved_at: '2026-06-08T11:00:00',
          reason: '实验失败',
        } as Decision,
      },
    })

    // cancelled: 无 button
    expect(wrapper.findAll(byTestid('option-btn'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('defer-btn'))).toHaveLength(0)
    expect(wrapper.findAll(byTestid('cancel-btn'))).toHaveLength(0)
    // cancelled: status-badge 1 (含 status-cancelled class, cancelled 在 map L110)
    // + readonly-hint 1 (走 v-else L59 + 三元 fallback 'cancelled' ? '取消' : '推迟')
    const statusBadge = wrapper.find(byTestid('status-cancelled'))
    expect(statusBadge.exists()).toBe(true)
    expect(statusBadge.classes()).toContain('status-cancelled')
    const readonlyHint = wrapper.find(byTestid('readonly-hint'))
    expect(readonlyHint.exists()).toBe(true)
    expect(readonlyHint.text()).toContain('取消')
    // cancelled: meta-info 走 cancelled 分支 ("取消原因" 而非 "推迟原因")
    const metaInfo = wrapper.find(byTestid('meta-info'))
    expect(metaInfo.exists()).toBe(true)
    expect(metaInfo.text()).toContain('取消原因: 实验失败')
  })
})
