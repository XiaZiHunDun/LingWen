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
    ...actual,
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
    setWizardDeepLink: vi.fn(),
    buildWizardShareUrl: vi.fn(),
    navigateTo: vi.fn(),
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

    await wrapper.find(byTestid('creator-workspace-tab-pulse')).trigger('click')
    await flushPromises()

    expect(wrapper.find(byTestid('column-pulse')).isVisible()).toBe(true)
    expect(wrapper.find(byTestid('volume-plan-panel')).exists()).toBe(true)
  })

  test('companion hides capability matrix until advanced panel opened', async () => {
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
    expect(wrapper.find('[data-testid="creator-advanced-ops"]').exists()).toBe(true)
  })
})
