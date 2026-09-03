import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NoProjectOnboarding from '@/components/NoProjectOnboarding.vue'

describe('NoProjectOnboarding', () => {
  it('renders intro + init commands by default', () => {
    const wrapper = mount(NoProjectOnboarding, { props: {} })
    expect(wrapper.find('[data-testid="onboarding-cmd-init"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="onboarding-cmd-env"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('本地优先')
  })

  it('shows loading state while checking', () => {
    const wrapper = mount(NoProjectOnboarding, { props: { loading: true } })
    expect(wrapper.find('[data-testid="onboarding-loading"]').exists()).toBe(true)
    // No commands / refresh button while loading
    expect(wrapper.find('[data-testid="onboarding-cmd-init"]').exists()).toBe(false)
  })

  it('shows error + retry when backend unreachable', async () => {
    const wrapper = mount(NoProjectOnboarding, { props: { error: 'backend down' } })
    expect(wrapper.find('[data-testid="onboarding-error"]').text()).toContain('backend down')
    await wrapper.find('[class="onboarding__btn"]').trigger('click')
    expect(wrapper.emitted('refresh')).toBeTruthy()
  })

  it('emits refresh on primary button', async () => {
    const wrapper = mount(NoProjectOnboarding, { props: {} })
    await wrapper.find('[class~="onboarding__btn--primary"]').trigger('click')
    expect(wrapper.emitted('refresh')).toHaveLength(1)
  })
})