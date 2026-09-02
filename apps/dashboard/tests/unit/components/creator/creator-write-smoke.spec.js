/**
 * creator-write-smoke.spec.js — Layer 2 保护：组件挂载冒烟测试
 *
 * 验证所有书桌相关组件在正确 mock 数据下能正常渲染，不抛出运行时错误。
 * 如果组件代码中存在 null 访问（如 wb.agent.generating），此测试会失败。
 *
 * 关键设计：mock 数据使用 unwrapped 格式（不用 .value 包装），
 * 与 Pinia store 和 reactive context 的实际行为一致。
 * 在模板中，reactive 对象的 ref 属性会自动解包。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, reactive } from 'vue'
import CreatorWriteWorkbench from '../../../../src/components/creator/CreatorWriteWorkbench.vue'
import CreatorWriteChat from '../../../../src/components/creator/CreatorWriteChat.vue'
import CreatorWritePanelChat from '../../../../src/components/creator/CreatorWritePanelChat.vue'
import CreatorWriteFooter from '../../../../src/components/creator/CreatorWriteFooter.vue'
import { CREATOR_WRITE_KEY } from '../../../../src/components/creator/creatorWriteKey.js'

// CreatorWriteSidebar 在推进模式下渲染 CreatorBatchRhythm（内部复用 usePilotBatch），
// 冒烟测试通过 mock 避免真实 SSE / 网络请求。
vi.mock('@/composables/usePilotBatch', () => ({
  usePilotBatch: () => ({
    activeJob: { value: null },
    chapterEvents: { value: [] },
    isJobActive: { value: false },
    refreshActive: vi.fn(),
  }),
}))

/**
 * 创建与真实数据结构一致的 mock 上下文。
 * 使用 reactive() 包裹，确保 ref 属性在模板中自动解包。
 */
function createMockWriteContext(overrides = {}) {
  const intentText = ref('')
  return reactive({
    wb: {
      creationMode: ref('companion'),
      leftPanelCollapsed: ref(false),
      generateRunning: ref(false),
      humanFirstDesk: ref(false),
      workbenchEnabled: ref(true),

      agent: {
        generating: ref(false),
        chat: vi.fn().mockResolvedValue('AI 回复'),
        ask: vi.fn().mockResolvedValue('AI 回复'),
        candidates: ref([]),
        directorAdvice: ref([]),
        statusLine: ref(''),
        runPlan: vi.fn(),
      },

      intentText,
      intentMood: ref(''),
      intentType: ref(''),
      intentTheme: ref(''),
      intentHistory: ref([]),

      startQuickWrite: vi.fn(),
      stopGenerate: vi.fn(),
      saveDraft: vi.fn(),
      updateCreationMode: vi.fn(),
      openOutline: vi.fn(),
      openStats: vi.fn(),

      goalCardLines: { line1: '测试项目', line2: '陪写模式', line3: '选路径→预览→确认' },
      consistencyItems: [],
      consistencyPanelOpen: ref(false),
      qualityHints: ref([]),
      chapterEntities: ref([]),
      inlineConflictMarkers: ref([]),
      showInlineConflictGutter: ref(false),
      lightValidationIssues: ref([]),
      lightValidationSummary: ref({ status: 'ok', label: '' }),
      lightValidationRunning: ref(false),
      bodySelection: ref({ start: 0, end: 0, text: '' }),
      hasBodySelection: ref(false),
      checkpoints: ref([]),
      diffCheckpointId: ref(null),
      diffView: ref(null),
      styleStrength: ref(1),
      selectionLocked: ref(false),
      allowWorldbuildingFill: ref(false),
      goalTag: ref(''),
      activeInlineConflictId: ref(null),
      chapterBodyConflictHighlightActive: ref(false),
      isPanelVisible: () => false,
      isLeftRailPanelVisible: () => false,
      isPanelCollapsed: () => true,
      captureBodySelection: vi.fn(),
      createCheckpoint: vi.fn(),
      restoreCheckpoint: vi.fn(),
      openCheckpointDiff: vi.fn(),
      closeCheckpointDiff: vi.fn(),
      toggleSelectionLock: vi.fn(),
      dismissQualityHint: vi.fn(),
      syncQualityFromLogicCheck: vi.fn(),
      focusInlineConflict: vi.fn(),
      focusLightValidationIssue: vi.fn(),
      clearInlineConflictFocus: vi.fn(),
      runLightValidationNow: vi.fn(),
      scheduleLightValidation: vi.fn(),
      saveIntentToHistory: vi.fn(),
      loadIntentFromHistory: vi.fn(),
      clearIntentHistory: vi.fn(),
      ...overrides,
    },
    overview: {
      chapters_written: 3,
      max_chapter: 36,
      name: '测试项目',
      creation_mode: 'companion',
    },
    chapterBodyDraft: ref(''),
    selectedChapter: ref(1),
    chapterOutlineDraft: ref(''),
    chapterOutlineSaving: ref(false),
    chapterBodySaving: ref(false),
    chapterBodyHighlightActive: ref(false),
    bodySaveStatusLabel: ref('已保存'),
    bodyAutoSaveStatus: ref('ok'),
    chapterPreview: ref(null),
    previewLoading: ref(false),
    chapterRecheckResult: ref(null),
    activeRecheckIssueIdx: ref(null),
    visibleChapters: [],
    chapterRowClass: () => '',
    chapterVolumeLabel: () => '',
    chapterRowTitle: () => '',
    showCompanionLogicCheckInWrite: false,
    logicCheckRunning: false,
    logicCheckResult: null,
    activeLogicCheckIssueIdx: ref(null),
    batchDeviationInlineSummary: null,
    deviationHighlightEnabled: false,
    highlightedDeviationChapter: null,
    openOutline: vi.fn(),
    openStats: vi.fn(),
    handleDeviationClick: vi.fn(),
    handleLogicCheckIssueClick: vi.fn(),
    onLogicCheckIssueKeydown: vi.fn(),
    onRecheckIssueKeydown: vi.fn(),
    focusIssueParagraph: vi.fn(),
    syncMemoryAssets: vi.fn(),
    bindChapterBodyTextareaRef: vi.fn(),
    saveChapterBody: vi.fn(),
    saveChapterOutline: vi.fn(),
    selectChapter: vi.fn(),
    runCompanionLogicCheck: vi.fn(),
    openVolumeSummaryForRange: vi.fn(),
    dismissBatchDeviationInlineSummary: vi.fn(),
  })
}

describe('Creator Write Components Smoke Test (Layer 2)', () => {
  let mockContext

  beforeEach(() => {
    vi.clearAllMocks()
    mockContext = createMockWriteContext()
  })

  describe('CreatorWriteWorkbench', () => {
    it('渲染时不抛出错误', () => {
      const wrapper = mount(CreatorWriteWorkbench, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: mockContext },
        },
        slots: {
          default: '<div class="test-editor">编辑器内容</div>',
          chapters: '<div class="test-chapters">章节列表</div>',
        },
      })
      expect(wrapper.find('.writer-desk').exists()).toBe(true)
    })

    it('空状态显示开始写作按钮', () => {
      mockContext.chapterBodyDraft = ''
      const wrapper = mount(CreatorWriteWorkbench, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: mockContext },
        },
        slots: {
          default: '<div class="test-editor">编辑器内容</div>',
          chapters: '<div class="test-chapters">章节列表</div>',
        },
      })
      expect(wrapper.find('.writer-desk__empty-state').exists()).toBe(true)
      expect(wrapper.find('.writer-desk__empty-state-btn').exists()).toBe(true)
    })

    it('点击开始写作按钮触发 startQuickWrite', async () => {
      mockContext.chapterBodyDraft = ''
      const wrapper = mount(CreatorWriteWorkbench, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: mockContext },
        },
        slots: {
          default: '<div class="test-editor">编辑器内容</div>',
          chapters: '<div class="test-chapters">章节列表</div>',
        },
      })
      await wrapper.find('.writer-desk__empty-state-btn').trigger('click')
      expect(mockContext.wb.startQuickWrite).toHaveBeenCalled()
    })

    it('advance 模式下正常渲染', () => {
      const advCtx = createMockWriteContext()
      advCtx.wb.creationMode = 'advance'
      const wrapper = mount(CreatorWriteWorkbench, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: advCtx },
        },
        slots: {
          default: '<div class="test-editor">编辑器内容</div>',
          chapters: '<div class="test-chapters">章节列表</div>',
        },
      })
      expect(wrapper.find('.writer-desk').exists()).toBe(true)
    })

    it('studio 模式下正常渲染', () => {
      const studioCtx = createMockWriteContext()
      studioCtx.wb.creationMode = 'studio'
      const wrapper = mount(CreatorWriteWorkbench, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: studioCtx },
        },
        slots: {
          default: '<div class="test-editor">编辑器内容</div>',
          chapters: '<div class="test-chapters">章节列表</div>',
        },
      })
      expect(wrapper.find('.writer-desk').exists()).toBe(true)
    })

    it('agent 生成中时 Footer 按钮禁用', () => {
      const busyCtx = createMockWriteContext()
      busyCtx.wb.agent.generating = true
      busyCtx.wb.generateRunning = true
      const wrapper = mount(CreatorWriteWorkbench, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: busyCtx },
        },
        slots: {
          default: '<div class="test-editor">编辑器内容</div>',
          chapters: '<div class="test-chapters">章节列表</div>',
        },
      })
      const generateBtn = wrapper.find('.writer-desk__generate-btn')
      expect(generateBtn.attributes('disabled')).toBeDefined()
    })
  })

  describe('CreatorWriteChat', () => {
    it('渲染时不抛出错误', () => {
      const wrapper = mount(CreatorWriteChat, {
        props: { showChatPanel: true },
        global: {
          provide: { [CREATOR_WRITE_KEY]: mockContext },
        },
      })
      expect(wrapper.find('.writer-desk__chat-panel').exists()).toBe(true)
    })

    it('agent 生成中时显示思考状态', () => {
      const busyCtx = createMockWriteContext()
      busyCtx.wb.agent.generating = true
      const wrapper = mount(CreatorWriteChat, {
        props: { showChatPanel: true },
        global: {
          provide: { [CREATOR_WRITE_KEY]: busyCtx },
        },
      })
      expect(wrapper.find('.writer-desk__chat-typing').exists()).toBe(true)
    })

    it('agent 生成中时发送按钮禁用', () => {
      const busyCtx = createMockWriteContext()
      busyCtx.wb.agent.generating = true
      const wrapper = mount(CreatorWriteChat, {
        props: { showChatPanel: true },
        global: {
          provide: { [CREATOR_WRITE_KEY]: busyCtx },
        },
      })
      const sendBtn = wrapper.find('.writer-desk__chat-send')
      expect(sendBtn.attributes('disabled')).toBeDefined()
    })
  })

  describe('CreatorWritePanelChat', () => {
    it('渲染时不抛出错误', () => {
      const wrapper = mount(CreatorWritePanelChat, {
        props: { showChatPanel: true },
        global: {
          provide: { [CREATOR_WRITE_KEY]: mockContext },
        },
      })
      expect(wrapper.find('.write-workbench__chat-panel').exists()).toBe(true)
    })

    it('agent 生成中时显示思考状态', () => {
      const busyCtx = createMockWriteContext()
      busyCtx.wb.agent.generating = true
      const wrapper = mount(CreatorWritePanelChat, {
        props: { showChatPanel: true },
        global: {
          provide: { [CREATOR_WRITE_KEY]: busyCtx },
        },
      })
      expect(wrapper.find('.write-workbench__chat-typing').exists()).toBe(true)
    })
  })

  describe('CreatorWriteFooter', () => {
    it('渲染时不抛出错误', () => {
      const wrapper = mount(CreatorWriteFooter, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: mockContext },
        },
      })
      expect(wrapper.find('.writer-desk__footer').exists()).toBe(true)
    })

    it('agent 生成中时 AI 续写按钮禁用', () => {
      const busyCtx = createMockWriteContext()
      busyCtx.wb.generateRunning = true
      busyCtx.wb.agent.generating = true
      const wrapper = mount(CreatorWriteFooter, {
        global: {
          provide: { [CREATOR_WRITE_KEY]: busyCtx },
        },
      })
      const generateBtn = wrapper.find('.writer-desk__generate-btn')
      expect(generateBtn.attributes('disabled')).toBeDefined()
    })
  })
})
