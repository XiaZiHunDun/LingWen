// tests/unit/chapter-table.spec.ts — Phase 9.57 F48
import { describe, test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChapterTable from '../../src/components/ChapterTable.vue'
import { byTestid } from '../helpers/by-testid'

const chapters = [
  { chapter: 2, hook_count: 1, hook_strength_avg: 0.2, coolpoint_count: 3, coolpoint_density: 0.1 },
  { chapter: 1, hook_count: 2, hook_strength_avg: null, coolpoint_count: 1, coolpoint_density: 0.05 },
]

describe('ChapterTable (F48)', () => {
  test('renders rows and sorts by chapter asc', () => {
    const wrapper = mount(ChapterTable, { props: { chapters } })
    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBe(2)
    expect(rows[0].text()).toContain('1')
  })

  test('click header toggles sort order', async () => {
    const wrapper = mount(ChapterTable, { props: { chapters } })
    const headers = wrapper.findAll('th')
    await headers[0].trigger('click')
    expect(wrapper.text()).toContain('▼')
  })

  test('empty chapters shows empty state', () => {
    const wrapper = mount(ChapterTable, { props: { chapters: [] } })
    expect(wrapper.find(byTestid('chapter-table')).exists()).toBe(true)
    expect(wrapper.text()).toContain('暂无章节数据')
  })

  test('formatPercent shows dash for null', () => {
    const wrapper = mount(ChapterTable, { props: { chapters } })
    expect(wrapper.text()).toContain('-')
  })
})
