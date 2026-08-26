import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WriteWorkspaceHeader from '@/components/writeWorkspace/WriteWorkspaceHeader.vue'

describe('WriteWorkspaceHeader', () => {
  it('renders chapter title and number', () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: '灰烬中的回声', mode: 'author', totalWords: 2830, dailyGoal: 3000 },
    })
    expect(wrapper.text()).toContain('第 12 章')
    expect(wrapper.text()).toContain('灰烬中的回声')
  })

  it('shows progress percentage', () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: 't', mode: 'author', totalWords: 1500, dailyGoal: 3000 },
    })
    expect(wrapper.text()).toContain('50%')
  })

  it('emits toggle-mode when switch clicked', async () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: 't', mode: 'author', totalWords: 0, dailyGoal: 3000 },
    })
    await wrapper.find('[data-testid="mode-toggle"]').trigger('click')
    expect(wrapper.emitted('toggleMode')).toBeTruthy()
  })

  it('shows Editor label when mode=editor', () => {
    const wrapper = mount(WriteWorkspaceHeader, {
      props: { chapterNumber: 12, title: 't', mode: 'editor', totalWords: 0, dailyGoal: 3000 },
    })
    expect(wrapper.text()).toContain('Editor')
  })
})