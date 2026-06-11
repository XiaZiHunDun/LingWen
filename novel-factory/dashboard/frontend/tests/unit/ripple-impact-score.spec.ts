// tests/unit/ripple-impact-score.spec.ts — Phase 9.59 F50
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'
import RippleCard from '../../src/components/RippleCard.vue'
import RippleFilter from '../../src/components/RippleFilter.vue'

describe('Ripple impact score UI (F50)', () => {
  test('RippleCard shows impact_score badge', () => {
    const wrapper = mount(RippleCard, {
      props: {
        ripple: {
          ripple_id: 'r1',
          dimension: 'character',
          relationship_type: 'causes',
          source_chapter: 1,
          target_chapter: 2,
          status: 'pending',
          confidence: 4,
          impact_score: 42.5,
        },
      },
    })
    const badge = wrapper.find(byTestid('ripple-impact-score'))
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toContain('42.5')
  })

  test('RippleFilter emits sortBy impact_score', async () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' },
    })
    await wrapper.find(byTestid('ripple-filter-sort')).setValue('impact_score')
    expect(wrapper.emitted('update:sortBy')?.[0]).toEqual(['impact_score'])
  })

  test('RippleFilter emits minScore from input', async () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' },
    })
    const input = wrapper.find(byTestid('ripple-filter-min-score'))
    await input.setValue('10')
    expect(wrapper.emitted('update:minScore')?.length).toBeGreaterThan(0)
  })
})
