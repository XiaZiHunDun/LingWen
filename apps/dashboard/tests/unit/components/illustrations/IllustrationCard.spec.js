import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IllustrationCard from '@/components/illustrations/IllustrationCard.vue'

describe('IllustrationCard', () => {
  const asset = {
    id: 'abc',
    type: 'chapter',
    chapter_num: 17,
    style_preset: 'ink',
    url: '/api/illustrations/abc/image?project_slug=test',
  }

  it('renders asset thumbnail', () => {
    const wrapper = mount(IllustrationCard, { props: { asset } })
    const img = wrapper.find('img[data-testid="illustration-thumb"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toContain('abc')
  })

  it('shows chapter number badge', () => {
    const wrapper = mount(IllustrationCard, { props: { asset } })
    expect(wrapper.text()).toContain('第 17 章')
  })

  it('shows cover badge for type=cover', () => {
    const coverAsset = { ...asset, id: 'cov', type: 'cover', chapter_num: null }
    const wrapper = mount(IllustrationCard, { props: { asset: coverAsset } })
    expect(wrapper.text()).toContain('封面')
    expect(wrapper.text()).not.toContain('第')
  })

  it('reactive: re-renders when asset prop changes', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset } })
    expect(wrapper.text()).toContain('第 17 章')
    await wrapper.setProps({ asset: { ...asset, chapter_num: 42 } })
    expect(wrapper.text()).toContain('第 42 章')
  })

  it('emits regenerate event on button click', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset } })
    await wrapper.find('[data-testid="regenerate-btn"]').trigger('click')
    expect(wrapper.emitted('regenerate')).toBeTruthy()
    expect(wrapper.emitted('regenerate')[0]).toEqual(['abc'])
  })

  it('emits delete event on button click', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset } })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')[0]).toEqual(['abc'])
  })

  it('buttons have aria-labels for screen readers', () => {
    const wrapper = mount(IllustrationCard, { props: { asset } })
    expect(wrapper.find('[data-testid="regenerate-btn"]').attributes('aria-label')).toBe(
      '重生 第 17 章'
    )
    expect(wrapper.find('[data-testid="delete-btn"]').attributes('aria-label')).toBe(
      '删除 第 17 章'
    )
  })
})
