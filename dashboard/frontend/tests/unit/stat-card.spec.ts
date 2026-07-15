// tests/unit/stat-card.spec.ts — Phase 9.57 F48
import { describe, test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'
import StatCard from '../../src/components/StatCard.vue'

describe('StatCard (F48)', () => {
  test('renders label and value', () => {
    const wrapper = mount(StatCard, { props: { label: 'Tokens', value: 1200 } })
    expect(wrapper.find(byTestid('stat-card')).text()).toContain('Tokens')
    expect(wrapper.find(byTestid('stat-card')).text()).toContain('1200')
  })

  test('positive trend class', () => {
    const wrapper = mount(StatCard, { props: { label: 'Cost', value: 3, trend: 5 } })
    expect(wrapper.find('.trend-positive').exists()).toBe(true)
    expect(wrapper.text()).toContain('+5%')
  })

  test('negative trend class', () => {
    const wrapper = mount(StatCard, { props: { label: 'Cost', value: 3, trend: -2 } })
    expect(wrapper.find('.trend-negative').exists()).toBe(true)
    expect(wrapper.text()).toContain('-2%')
  })
})
