import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
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

// Phase 106: NPopconfirm wrapping around 🗑 delete button (RED-state tests).
// These tests assume NPopconfirm wraps the 🗑 button (C8). Currently the
// delete-btn emits directly on click (see "emits delete event on button click"
// above), so F1 + F3 fail in RED state for the right reason; F2 + F4 may pass
// coincidentally because direct click behavior already meets the assertions.
describe('IllustrationCard (Phase 106: NPopconfirm delete)', () => {
  const popconfirmAsset = {
    id: 'a1',
    type: 'cover',
    chapter_num: null,
    style_preset: 'ink',
    url: '/api/illustrations/a1/image?project_slug=test',
  }

  it('F1: clicking 🗑 button opens NPopconfirm', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset: { ...popconfirmAsset, id: 'a1' } } })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    expect(document.body.textContent).toContain('确定删除这张插图？')
  })

  it('F2: clicking "确认删除" emits delete event with asset.id', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset: { ...popconfirmAsset, id: 'a2' } } })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    const confirmBtn = document.body.querySelector(
      '.n-popconfirm__action .n-button--primary-type'
    )
    if (confirmBtn) confirmBtn.click()
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')[0]).toEqual(['a2'])
  })

  it('F3: clicking "取消" does NOT emit delete event', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset: { ...popconfirmAsset, id: 'a3' } } })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    const cancelBtn = document.body.querySelector(
      '.n-popconfirm__action .n-button:not(.n-button--primary-type)'
    )
    if (cancelBtn) cancelBtn.click()
    expect(wrapper.emitted('delete')).toBeFalsy()
  })

  it('F4: Esc key dismisses popconfirm', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset: { ...popconfirmAsset, id: 'a4' } } })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()
    expect(document.body.textContent).not.toContain('确定删除这张插图？')
  })
})
