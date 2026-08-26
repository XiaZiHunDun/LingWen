import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceConflictDialog from '@/components/writeWorkspace/WriteWorkspaceConflictDialog.vue'

describe('WriteWorkspaceConflictDialog', () => {
  it('shows 3 options when open', () => {
    const wrapper = mount(WriteWorkspaceConflictDialog, { props: { open: true, externalMtime: 1234567890 } })
    expect(wrapper.text()).toMatch(/rebase/i)
    expect(wrapper.text()).toContain('放弃本地')
    expect(wrapper.text()).toContain('导出本地')
  })

  it('emits rebase, discard, export on button clicks', async () => {
    const wrapper = mount(WriteWorkspaceConflictDialog, { props: { open: true, externalMtime: 1234567890 } })
    await wrapper.find('[data-testid="rebase-btn"]').trigger('click')
    expect(wrapper.emitted('rebase')).toBeTruthy()
    await wrapper.find('[data-testid="discard-btn"]').trigger('click')
    expect(wrapper.emitted('discard')).toBeTruthy()
    await wrapper.find('[data-testid="export-btn"]').trigger('click')
    expect(wrapper.emitted('export')).toBeTruthy()
  })
})