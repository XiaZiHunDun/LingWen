// tests/unit/creator-workspace.spec.ts — Phase C workspace tabs

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

const creatorMocks = vi.hoisted(() => ({
  fetchCreatorOverview: vi.fn(),
  loadVolumePlan: vi.fn(),
  fetchCreatorOnboarding: vi.fn(),
}))

vi.mock('../../src/api/index.js', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...(actual as object),
    fetchCreatorOverview: creatorMocks.fetchCreatorOverview,
    fetchCreatorVolumePlan: vi.fn().mockResolvedValue({ volumes: [] }),
    fetchCreatorSettingsDocs: vi.fn().mockResolvedValue({
      pillars_text: '',
      global_outline_text: '',
      pillars_revision: 1,
      global_outline_revision: 1,
    }),
    fetchCreatorSettingsHistory: vi.fn().mockResolvedValue({ snapshots: [] }),
    fetchCreatorVolumeTemplates: vi.fn().mockResolvedValue({ templates: [] }),
    fetchCreatorTemplateSyncSources: vi.fn().mockResolvedValue({ sources: [] }),
    fetchCreatorOnboarding: creatorMocks.fetchCreatorOnboarding,
    fetchCreatorMergePreferences: vi.fn().mockResolvedValue({}),
    fetchCreatorMergePresetPackages: vi.fn().mockResolvedValue({ packages: [] }),
    fetchCreatorTemplateApprovals: vi.fn().mockResolvedValue({ pending: [], history: [] }),
    fetchStudioActiveBatchJob: vi.fn().mockResolvedValue(null),
    fetchCreatorBatchHistory: vi.fn().mockResolvedValue({ items: [] }),
    fetchCreatorDiffCollabNotes: vi.fn().mockResolvedValue({ notes: {} }),
    previewCreatorVolumePlanDiff: vi.fn().mockResolvedValue({ changes: [] }),
    fetchCreatorPreferences: vi.fn().mockResolvedValue({
      default_model: 'minimax-abab6.5',
      temperature: 0.7,
      max_tokens: 8000,
      memory_rag_enabled: true,
      memory_rag_top_k: 8,
      task_models: {},
      companion_lightweight: true,
    }),
    fetchCreatorMemoryAssets: vi.fn().mockResolvedValue({
      memory_available: true,
      memory_rag_enabled: true,
      items: [],
    }),
    fetchCreatorModels: vi.fn().mockResolvedValue({
      models: [{ id: 'local-mock', label: '本地 Mock', provider: 'mock', available: true }],
      default_model: 'local-mock',
    }),
  }
})

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({ projectRevision: { value: 0 } }),
}))

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    focusWizard: { value: false },
    focusWizardStep: { value: null },
    focusWizardDone: { value: [] },
    focusWizardNotes: { value: {} },
    focusCreatorWorkspace: { value: null },
    setWizardDeepLink: vi.fn(),
    buildWizardShareUrl: vi.fn(),
    navigateTo: vi.fn(),
    setCreatorWorkspace: vi.fn(),
  }),
}))

import CreatorPage from '../../src/pages/CreatorPage.vue'

const companionOverview = {
  slug: 'demo',
  name: '演示',
  creation_mode: 'companion',
  max_chapter: 5,
  chapters_written: 0,
  coverage_pct: 0,
  chapters: [
    { chapter: 1, has_body: false, has_outline: false, word_count: 0, excerpt: null },
  ],
  volume_summaries: [],
  deviations: [],
  deviation_count: 0,
  alert_count: 0,
  ui_profile: {
    creation_mode: 'companion',
    creator_workspace_tabs: true,
    creator_mode_guide_default_collapsed: true,
    chapter_inline_edit: true,
    chapter_full_preview: false,
    wizard_default_collapsed: true,
    volume_pulse_enabled: false,
    show_studio_workflow: false,
    simplified_notifications: true,
  },
  volume_pulse: null,
}

describe('Creator workspace tabs (Phase C)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    creatorMocks.fetchCreatorOverview.mockResolvedValue(companionOverview)
    creatorMocks.fetchCreatorOnboarding.mockResolvedValue(null)
  })

  test('companion shows workspace tabs with write column only', async () => {
    const wrapper = mount(CreatorPage)
    await flushPromises()

    expect(wrapper.find(byTestid('creator-workspace-tabs')).exists()).toBe(true)
    expect(wrapper.find(byTestid('column-write')).isVisible()).toBe(true)
    expect(wrapper.find(byTestid('column-pulse')).isVisible()).toBe(false)
    expect(wrapper.find(byTestid('column-settings')).isVisible()).toBe(false)
  })

  test('studio mode opens pulse tab and hides write tab', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      ...companionOverview,
      creation_mode: 'studio',
      ui_profile: {
        ...companionOverview.ui_profile,
        creation_mode: 'studio',
        show_studio_workflow: true,
        volume_pulse_enabled: true,
      },
      volume_pulse: {
        volume_count: 1,
        alert_count: 0,
        overall_status: 'ok',
        alerts_only: true,
        volumes: [{
          label: '一',
          start_chapter: 1,
          end_chapter: 5,
          written: 0,
          total_chapters: 5,
          progress_pct: 0,
          locked: false,
          status: 'ok',
          deviation_count: 0,
          headline: '未开始',
        }],
      },
    })
    const wrapper = mount(CreatorPage)
    await flushPromises()
    expect(wrapper.find(byTestid('creator-workspace-tabs')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-workspace-tab-write')).exists()).toBe(false)
    expect(wrapper.find(byTestid('column-pulse')).isVisible()).toBe(true)
    expect(wrapper.find(byTestid('column-write')).isVisible()).toBe(false)
  })

  test('advance mode defaults to write tab with workbench', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      ...companionOverview,
      creation_mode: 'advance',
      ui_profile: {
        ...companionOverview.ui_profile,
        creation_mode: 'advance',
        volume_pulse_enabled: true,
        chapter_inline_edit: true,
        chapter_outline_inline_edit: true,
        creator_write_workbench: true,
      },
      volume_pulse: {
        volume_count: 1,
        alert_count: 0,
        overall_status: 'ok',
        alerts_only: true,
        volumes: [{
          label: '一',
          start_chapter: 1,
          end_chapter: 5,
          written: 0,
          total_chapters: 5,
          progress_pct: 0,
          locked: false,
          status: 'ok',
          deviation_count: 0,
          headline: '未开始',
        }],
      },
    })
    const wrapper = mount(CreatorPage)
    await flushPromises()
    expect(wrapper.find(byTestid('column-write')).isVisible()).toBe(true)
    expect(wrapper.find(byTestid('column-pulse')).isVisible()).toBe(false)
    expect(wrapper.find(byTestid('creator-write-workbench')).exists()).toBe(true)
    expect(wrapper.find(byTestid('write-chapter-rail')).exists()).toBe(true)
    expect(wrapper.find(byTestid('write-advanced-tools')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creation-mode-badge')).exists()).toBe(false)
    expect(wrapper.find(byTestid('creator-workspace-secondary-tabs')).exists()).toBe(true)
    expect(wrapper.find(byTestid('export-btn')).exists()).toBe(false)
  })

  test('human-first desk hides duplicate page title and preferences', async () => {
    const wrapper = mount(CreatorPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).exists()).toBe(false)
    expect(wrapper.find(byTestid('creator-preferences-summary')).exists()).toBe(false)
    expect(wrapper.find(byTestid('creator-workspace-secondary-tabs')).exists()).toBe(true)
  })

  test('settings advanced section is collapsed by default', async () => {
    const wrapper = mount(CreatorPage)
    await flushPromises()
    await wrapper.find(byTestid('creator-workspace-tab-settings')).trigger('click')
    await flushPromises()
    const advanced = wrapper.find(byTestid('settings-advanced-section'))
    expect(advanced.exists()).toBe(true)
    expect((advanced.element as HTMLDetailsElement).open).toBe(false)
  })

  test('pulse tab reveals volume plan area for advance profile', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      ...companionOverview,
      creation_mode: 'advance',
      advance_volume_summary: true,
      ui_profile: {
        ...companionOverview.ui_profile,
        creation_mode: 'advance',
        creator_workspace_tabs: true,
        volume_pulse_enabled: true,
      },
      volume_pulse: {
        volume_count: 1,
        alert_count: 0,
        overall_status: 'ok',
        alerts_only: true,
        volumes: [{
          label: '一',
          start_chapter: 1,
          end_chapter: 5,
          written: 0,
          total_chapters: 5,
          progress_pct: 0,
          locked: false,
          status: 'ok',
          deviation_count: 0,
          headline: '未开始',
        }],
      },
    })
    const wrapper = mount(CreatorPage)
    await flushPromises()

    await wrapper.find(byTestid('creator-desk-drawer-pulse')).trigger('click')
    await flushPromises()

    expect(wrapper.find(byTestid('column-pulse')).isVisible()).toBe(true)
    expect(wrapper.find(byTestid('volume-plan-panel')).exists()).toBe(true)
  })

  test('companion hides mode guide and capability matrix chrome', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      ...companionOverview,
      ui_profile: {
        ...companionOverview.ui_profile,
        creation_mode_capability_matrix: true,
        creator_simplified_mode_ops: true,
      },
    })
    const wrapper = mount(CreatorPage)
    await flushPromises()
    expect(wrapper.find('[data-testid="creation-mode-capability-matrix"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="creator-mode-guide-panel"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="creator-advanced-ops"]').exists()).toBe(false)
  })

  test('companion shows logic check in write tab when primary_action is logic_check', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      ...companionOverview,
      ui_profile: {
        ...companionOverview.ui_profile,
        primary_action: 'logic_check',
      },
    })
    const wrapper = mount(CreatorPage)
    await flushPromises()
    expect(wrapper.find(byTestid('companion-logic-check-write')).exists()).toBe(true)
    expect(wrapper.find(byTestid('companion-logic-check-panel')).exists()).toBe(false)
    expect(wrapper.find(byTestid('run-companion-logic-check-btn')).exists()).toBe(true)
  })

  test('companion shows desk drawer triggers and micro task bar', async () => {
    const wrapper = mount(CreatorPage)
    await flushPromises()
    expect(wrapper.find(byTestid('creator-desk-drawer-triggers')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-desk-drawer-pulse')).exists()).toBe(true)
    expect(wrapper.find(byTestid('write-micro-task-bar')).exists()).toBe(true)
    expect(wrapper.find(byTestid('creator-workspace-tab-pulse')).exists()).toBe(false)
  })

  test('companion pulse tab shows empty guide when no volumes or deviations', async () => {
    const wrapper = mount(CreatorPage)
    await flushPromises()
    await wrapper.find(byTestid('creator-desk-drawer-pulse')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('pulse-empty-guide')).exists()).toBe(true)
  })

  test('pulse tab badge shows deviation count', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      ...companionOverview,
      deviation_count: 2,
      alert_count: 1,
      deviations: [
        { type: 'missing_body', severity: 'warn', chapter: 2, message: '缺正文' },
      ],
      ui_profile: {
        ...companionOverview.ui_profile,
        deviation_min_severity: null,
      },
    })
    const wrapper = mount(CreatorPage)
    await flushPromises()
    const badge = wrapper.find(byTestid('creator-desk-drawer-pulse')).find('.hub-tab-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('2')
  })

  test('mode guide panel follows creator grid in DOM order', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValueOnce({
      ...companionOverview,
      creation_mode: 'advance',
      ui_profile: {
        ...companionOverview.ui_profile,
        creation_mode: 'advance',
      },
    })
    const wrapper = mount(CreatorPage)
    await flushPromises()
    const grid = wrapper.find(byTestid('creator-grid')).element
    const guide = wrapper.find(byTestid('creator-mode-guide-panel')).element
    expect(grid.compareDocumentPosition(guide) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })
})
