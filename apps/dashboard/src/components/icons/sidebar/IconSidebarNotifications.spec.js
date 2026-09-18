import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IconSidebarNotifications from './IconSidebarNotifications.vue'

describe('IconSidebarNotifications', () => {
  it('renders with viewBox + ≥2 paths and accent fill', () => {
    const wrapper = mount(IconSidebarNotifications)
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
    expect(svg.attributes('viewBox')).toBeTruthy()
    const paths = wrapper.findAll('path')
    expect(paths.length).toBeGreaterThanOrEqual(2)
    const accentPath = paths.find((p) => p.attributes('fill')?.includes('--lingwen-icon-accent'))
    expect(accentPath).toBeTruthy()
  })
})
