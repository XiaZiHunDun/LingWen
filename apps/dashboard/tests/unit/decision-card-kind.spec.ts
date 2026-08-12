// tests/unit/decision-card-kind.spec.ts — Phase 8.38
// 7 kind testid: decision-kind-outline-judgment / -volume-judgment / -chapter-iteration-judgment
//   / -publish-judgment / -subplot-open / -subplot-close / -style-pick
// 加到 7 kind class badge 元素 (1:1 镜像), 走 byTestid helper (Phase 8.35).
// Phase 8.32 加 6 inner testid (status-badge / option-btn / defer-btn / cancel-btn /
// readonly-hint / meta-info), kind badge 0 testid. Phase 8.38 收尾 kind badge 1:1
// testid 镜像, e2e 找特定 kind 节点得 .find('.kind-outline-judgment') 脆 selector,
// 改 byTestid 稳定 selector.

import { describe, test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'
import DecisionCard from '../../src/components/DecisionCard.vue'

const kinds = [
  'outline_judgment',
  'volume_judgment',
  'chapter_iteration_judgment',
  'publish_judgment',
  'subplot_open',
  'subplot_close',
  'style_pick',
]

describe('DecisionCard — Phase 8.38 7 kind testid', () => {
  for (const kind of kinds) {
    test(`${kind} kind testid 在位 + 1:1 镜像 kind class`, () => {
      const kindClass = kind.replace(/_/g, '-')
      const wrapper = mount(DecisionCard, {
        props: {
          decision: {
            decision_id: 'd1',
            kind,
            status: 'pending',
            title: 'Test',
            description: 'Test',
            options: [],
          },
        },
      })
      const el = wrapper.find(byTestid(`decision-kind-${kindClass}`))
      expect(el.exists()).toBe(true)
      expect(el.classes()).toContain(`kind-${kindClass}`)
    })
  }
})
