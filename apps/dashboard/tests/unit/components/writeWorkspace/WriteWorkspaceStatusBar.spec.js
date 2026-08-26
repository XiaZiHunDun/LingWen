import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceStatusBar from '@/components/writeWorkspace/WriteWorkspaceStatusBar.vue'

describe('WriteWorkspaceStatusBar', () => {
  it('shows idle state by default', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'idle', lastSavedAt: null, dirty: false } } })
    expect(wrapper.text()).toContain('就绪')
  })

  it('shows saving state', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'saving', lastSavedAt: null, dirty: true } } })
    expect(wrapper.text()).toContain('保存中')
  })

  it('shows saved time', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'saved', lastSavedAt: '2026-08-26T14:32:11Z', dirty: false } } })
    expect(wrapper.text()).toMatch(/已保存/)
  })

  it('shows error state', () => {
    const wrapper = mount(WriteWorkspaceStatusBar, { props: { saveState: { status: 'error', lastSavedAt: null, dirty: true, errorMessage: 'disk full' } } })
    expect(wrapper.text()).toContain('错误')
    expect(wrapper.text()).toContain('disk full')
  })
})
