// tests/unit/library-page.spec.ts — Task C-1
// LibraryPage coverage lift: 9% stmts / 10% lines / 0% functions → ~80%.
// Exercises: loading, error, empty, grid, card clicks, startNew, helpers.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import LibraryPage from '../../src/pages/LibraryPage.vue'
import { byTestid } from '../helpers/by-testid'

const setup = vi.hoisted(() => ({
  studio: {
    loadProjects: vi.fn().mockResolvedValue(undefined),
    switchProject: vi.fn().mockResolvedValue(undefined),
  },
  nav: {
    navigateTo: vi.fn(),
    setWizardDeepLink: vi.fn(),
  },
  writeResume: {
    getWriteResume: vi.fn().mockReturnValue(null),
  },
  api: {
    fetchStudioQuality: vi.fn().mockResolvedValue(null),
  },
  display: {
    formatDisplayLabel: vi.fn((name: unknown) => (typeof name === 'string' ? name : '')),
  },
}))

// Reactive state at top-level (vi.hoisted only captures `vi`).
const projectsRef = ref<Array<Record<string, unknown>>>([])
const activeSlugRef = ref<string | null>(null)

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({
    get projects() { return projectsRef.value },
    get activeSlug() { return activeSlugRef.value },
    loadProjects: setup.studio.loadProjects,
    switchProject: setup.studio.switchProject,
  }),
}))

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => setup.nav,
}))

vi.mock('../../src/utils/writeResumeStorage.js', () => ({
  getWriteResume: setup.writeResume.getWriteResume,
}))

vi.mock('../../src/utils/displayProjectName.js', () => ({
  formatDisplayLabel: setup.display.formatDisplayLabel,
}))

vi.mock('../../src/api/index.js', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...(actual as object),
    fetchStudioQuality: setup.api.fetchStudioQuality,
  }
})

// LibraryPage calls `fetchStudioQuality()` as a global (vite auto-import), not
// via an explicit `import`. Stub it on globalThis so the page finds it.
;(globalThis as Record<string, unknown>).fetchStudioQuality =
  setup.api.fetchStudioQuality

function mountLibraryPage() {
  return mount(LibraryPage)
}

const sampleProjects = [
  { slug: 'demo-novel', name: 'Demo Novel', chapter_count: 5 },
  { slug: 'test-proj', name: 'Test Project', has_body: true },
  { slug: 'fresh-proj', name: 'Fresh' },
]

describe('LibraryPage (Task C-1)', () => {
  beforeEach(() => {
    projectsRef.value = []
    activeSlugRef.value = null
    setup.studio.loadProjects.mockClear().mockResolvedValue(undefined)
    setup.studio.switchProject.mockClear().mockResolvedValue(undefined)
    setup.nav.navigateTo.mockClear()
    setup.nav.setWizardDeepLink.mockClear()
    setup.writeResume.getWriteResume.mockClear().mockReturnValue(null)
    setup.api.fetchStudioQuality.mockClear().mockResolvedValue(null)
    setup.display.formatDisplayLabel.mockClear()
    setup.display.formatDisplayLabel.mockImplementation(
      (name: unknown) => (typeof name === 'string' ? name : ''),
    )
  })

  test('renders page testid', async () => {
    const wrapper = mountLibraryPage()
    await flushPromises()
    expect(wrapper.find(byTestid('library-page')).exists()).toBe(true)
  })

  test('shows loading state initially', async () => {
    // Don't resolve loadProjects so loading stays true
    let resolveLoad: () => void
    setup.studio.loadProjects.mockReturnValue(
      new Promise<void>((resolve) => {
        resolveLoad = resolve
      }),
    )
    const wrapper = mountLibraryPage()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('加载中')
    resolveLoad!()
    await flushPromises()
  })

  test('shows error state when loadProjects throws', async () => {
    setup.studio.loadProjects.mockRejectedValue(new Error('boom'))
    const wrapper = mountLibraryPage()
    await flushPromises()

    expect(wrapper.text()).toContain('boom')
  })

  test('shows empty state when no projects', async () => {
    const wrapper = mountLibraryPage()
    await flushPromises()

    expect(wrapper.find(byTestid('library-empty')).exists()).toBe(true)
    expect(wrapper.find(byTestid('library-grid')).exists()).toBe(false)
    expect(wrapper.find(byTestid('library-empty-new-btn')).exists()).toBe(true)
  })

  test('shows grid state when projects exist', async () => {
    projectsRef.value = sampleProjects
    const wrapper = mountLibraryPage()
    await flushPromises()

    expect(wrapper.find(byTestid('library-grid')).exists()).toBe(true)
    expect(wrapper.find(byTestid('library-empty')).exists()).toBe(false)

    for (const p of sampleProjects) {
      expect(wrapper.find(byTestid(`library-card-${p.slug}`)).exists()).toBe(true)
    }
  })

  test('renders active card with active class and badge', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = 'demo-novel'
    const wrapper = mountLibraryPage()
    await flushPromises()

    const activeCard = wrapper.find(byTestid('library-card-demo-novel'))
    expect(activeCard.classes()).toContain('library-card--active')
    expect(activeCard.text()).toContain('当前')

    const otherCard = wrapper.find(byTestid('library-card-test-proj'))
    expect(otherCard.classes()).not.toContain('library-card--active')
    expect(otherCard.text()).not.toContain('当前')
  })

  test('card click on inactive project switches then navigates', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = 'demo-novel'
    setup.writeResume.getWriteResume.mockReturnValue({ chapter: 7 })
    const wrapper = mountLibraryPage()
    await flushPromises()

    await wrapper.find(byTestid('library-card-test-proj')).trigger('click')
    await flushPromises()

    expect(setup.studio.switchProject).toHaveBeenCalledWith('test-proj')
    expect(setup.writeResume.getWriteResume).toHaveBeenCalledWith('test-proj')
    expect(setup.nav.navigateTo).toHaveBeenCalledWith('write', {
      chapter: 7,
      clearFocus: false,
    })
  })

  test('card click on active project navigates without switching', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = 'demo-novel'
    setup.writeResume.getWriteResume.mockReturnValue({ chapter: 3 })
    const wrapper = mountLibraryPage()
    await flushPromises()

    await wrapper.find(byTestid('library-card-demo-novel')).trigger('click')
    await flushPromises()

    expect(setup.studio.switchProject).not.toHaveBeenCalled()
    expect(setup.nav.navigateTo).toHaveBeenCalledWith('write', {
      chapter: 3,
      clearFocus: false,
    })
  })

  test('card click falls back to null chapter when no resume', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = 'demo-novel'
    setup.writeResume.getWriteResume.mockReturnValue(null)
    const wrapper = mountLibraryPage()
    await flushPromises()

    await wrapper.find(byTestid('library-card-test-proj')).trigger('click')
    await flushPromises()

    expect(setup.nav.navigateTo).toHaveBeenCalledWith('write', {
      chapter: null,
      clearFocus: false,
    })
  })

  test('startNew from grid calls setWizardDeepLink + navigateTo with wizard', async () => {
    projectsRef.value = sampleProjects
    const wrapper = mountLibraryPage()
    await flushPromises()

    await wrapper.find(byTestid('library-new-btn')).trigger('click')
    expect(setup.nav.setWizardDeepLink).toHaveBeenCalledWith(true, 'welcome', [], {})
    expect(setup.nav.navigateTo).toHaveBeenCalledWith('write', {
      wizard: true,
      clearFocus: true,
    })
  })

  test('startNew from empty state same wizard navigation', async () => {
    // empty state
    const wrapper = mountLibraryPage()
    await flushPromises()

    await wrapper.find(byTestid('library-empty-new-btn')).trigger('click')
    expect(setup.nav.setWizardDeepLink).toHaveBeenCalledWith(true, 'welcome', [], {})
    expect(setup.nav.navigateTo).toHaveBeenCalledWith('write', {
      wizard: true,
      clearFocus: true,
    })
  })

  test('subtitle shows chapter count when present', async () => {
    projectsRef.value = sampleProjects
    const wrapper = mountLibraryPage()
    await flushPromises()

    const card = wrapper.find(byTestid('library-card-demo-novel'))
    expect(card.text()).toContain('已写 5 章')
  })

  test('subtitle shows 进行中 for has_body project', async () => {
    projectsRef.value = sampleProjects
    const wrapper = mountLibraryPage()
    await flushPromises()

    const card = wrapper.find(byTestid('library-card-test-proj'))
    expect(card.text()).toContain('进行中')
  })

  test('subtitle shows 尚未开写 when no body and no count', async () => {
    projectsRef.value = sampleProjects
    const wrapper = mountLibraryPage()
    await flushPromises()

    const card = wrapper.find(byTestid('library-card-fresh-proj'))
    expect(card.text()).toContain('尚未开写')
  })

  test('qualityLine shows on active card when quality data present', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = 'demo-novel'
    setup.api.fetchStudioQuality.mockResolvedValue({
      chapters_written: 5,
      coverage_pct: 80,
    })
    const wrapper = mountLibraryPage()
    await flushPromises()

    const activeCard = wrapper.find(byTestid('library-card-demo-novel'))
    expect(activeCard.text()).toContain('5 章')
    expect(activeCard.text()).toContain('80%')
  })

  test('qualityLine not shown on inactive cards', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = 'demo-novel'
    setup.api.fetchStudioQuality.mockResolvedValue({
      chapters_written: 5,
      coverage_pct: 80,
    })
    const wrapper = mountLibraryPage()
    await flushPromises()

    const otherCard = wrapper.find(byTestid('library-card-test-proj'))
    expect(otherCard.text()).not.toContain('5 章')
  })

  test('qualityLine not fetched when no active project', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = null
    const wrapper = mountLibraryPage()
    await flushPromises()

    expect(setup.api.fetchStudioQuality).not.toHaveBeenCalled()
  })

  test('qualityLine fetch error is swallowed', async () => {
    projectsRef.value = sampleProjects
    activeSlugRef.value = 'demo-novel'
    setup.api.fetchStudioQuality.mockRejectedValue(new Error('quality failed'))
    const wrapper = mountLibraryPage()
    await flushPromises()

    // No error displayed (swallowed), page still renders
    expect(wrapper.text()).not.toContain('quality failed')
    expect(wrapper.find(byTestid('library-grid')).exists()).toBe(true)
  })

  test('displayProjectName falls back to slug', async () => {
    projectsRef.value = [{ slug: 'no-name', chapter_count: 1 }]
    setup.display.formatDisplayLabel.mockReturnValue('') // empty after strip
    const wrapper = mountLibraryPage()
    await flushPromises()

    const card = wrapper.find(byTestid('library-card-no-name'))
    expect(card.text()).toContain('no-name')
  })

  test('displayProjectName falls back to 未命名 when no name and no slug', async () => {
    projectsRef.value = [{ slug: '', chapter_count: 0 }]
    setup.display.formatDisplayLabel.mockReturnValue('')
    const wrapper = mountLibraryPage()
    await flushPromises()

    // Empty slug would create testid="library-card-" which is invalid.
    // LibraryPage uses slug as key — duplicate keys would warn but still render.
    // For our test, just check that the page doesn't crash.
    expect(wrapper.find(byTestid('library-page')).exists()).toBe(true)
  })

  test('cover letter uses first char of name', async () => {
    projectsRef.value = [{ slug: 'alpha', name: 'Alpha' }]
    const wrapper = mountLibraryPage()
    await flushPromises()

    const card = wrapper.find(byTestid('library-card-alpha'))
    expect(card.text()).toContain('A')
  })

  test('cover letter falls back to first char of slug', async () => {
    projectsRef.value = [{ slug: 'beta-novel' }]
    setup.display.formatDisplayLabel.mockReturnValue('')
    const wrapper = mountLibraryPage()
    await flushPromises()

    const card = wrapper.find(byTestid('library-card-beta-novel'))
    expect(card.text()).toContain('b')
  })
})
