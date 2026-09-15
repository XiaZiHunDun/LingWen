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
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    const img = wrapper.find('img[data-testid="illustration-thumb"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toContain('abc')
  })

  it('shows chapter number badge', () => {
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    expect(wrapper.text()).toContain('第 17 章')
  })

  it('emits regenerate event on button click', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    await wrapper.find('[data-testid="regenerate-btn"]').trigger('click')
    expect(wrapper.emitted('regenerate')).toBeTruthy()
    expect(wrapper.emitted('regenerate')[0]).toEqual(['abc'])
  })

  it('emits delete event on button click', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')[0]).toEqual(['abc'])
  })
})
