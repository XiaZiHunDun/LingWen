/**
 * Navigation Store - Manages dashboard navigation state
 *
 * @typedef {Object} NavStoreState
 * @property {string} activeNav - 当前活跃导航项
 * @property {string} produceTab - 生产页当前 tab
 * @property {string} inboxTab - 收件箱当前 tab
 * @property {string} insightTab - 洞察页当前 tab
 * @property {number|null} focusChapter - 当前聚焦章节
 * @property {string|null} focusDecisionId - 当前聚焦决策 ID
 * @property {boolean} focusWizard - 是否显示向导
 * @property {string|null} focusWizardStep - 向导当前步骤
 * @property {string[]} focusWizardDone - 向导已完成步骤
 * @property {Object} focusWizardNotes - 向导笔记
 * @property {string|null} focusCreatorWorkspace - 创作工作区
 *
 * 注意：Pinia store 属性已自动解包，不需要 .value。直接使用 navStore.activeNav 即可。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  LEGACY_INBOX_NAV_IDS,
  LEGACY_INSIGHT_NAV_IDS,
  LEGACY_PRODUCE_NAV_IDS,
  PRODUCE_TABS,
  INBOX_TABS,
  INSIGHT_TABS,
} from '../config/dashboardNav.js'
import {
  activeNavToUrlParam,
  resolveHumanNavToActive,
} from '../config/humanFirstNav.js'
import { useNavUrlUtils } from './useNavUrlUtils'

const PRODUCE_TAB_IDS = PRODUCE_TABS.map((t) => t.id)
const INBOX_TAB_IDS = INBOX_TABS.map((t) => t.id)
const INSIGHT_TAB_IDS = INSIGHT_TABS.map((t) => t.id)

const CREATOR_WORKSPACE_IDS = ['write', 'pulse', 'settings']

const VALID_NAV = [
  'ask',
  'write',
  'library',
  'more',
  'today',
  'creator',
  'produce',
  'inbox',
  'insight',
  'studio',
  'chapters',
  'workflows',
  'decisions',
  'ripples',
  'overview',
  'analytics',
  'cascade-runs',
  'settings',
]

const REVIEWER_BLOCKED_NAV = new Set([
  'write', 'creator', 'produce', 'library', 'more', 'settings', 'cascade-runs',
  'studio', 'chapters', 'workflows',
])

export const useNavStore = defineStore('nav', () => {
  const utils = useNavUrlUtils()

  const rawNavOnLoad = utils.readRawNavFromUrl()
  const initialNav = utils.readNavFromUrl()

  const activeNav = ref(initialNav ?? 'ask')
  const produceTab = ref(utils.readProduceTab(rawNavOnLoad))
  const inboxTab = ref(utils.readInboxTab(rawNavOnLoad))
  const insightTab = ref(utils.readInsightTab(rawNavOnLoad))
  const focusChapter = ref(utils.readChapterFromUrl())
  const focusDecisionId = ref(utils.readDecisionFromUrl())
  const focusWizard = ref(utils.readWizardFromUrl())
  const focusWizardStep = ref(utils.readWizardStepFromUrl())
  const focusWizardDone = ref(utils.readWizardDoneFromUrl())
  const focusWizardNotes = ref(utils.readWizardNotesFromUrl())
  const focusCreatorWorkspace = ref(utils.readCreatorWorkspaceFromUrl())

  function resolveNavTarget(nav) {
    if (nav === 'write' || nav === 'creator') {
      return { nav: 'creator' }
    }
    if (LEGACY_PRODUCE_NAV_IDS.includes(nav)) {
      return { nav: 'produce', produceTab: nav }
    }
    if (LEGACY_INBOX_NAV_IDS.includes(nav)) {
      return { nav: 'inbox', inboxTab: nav }
    }
    if (LEGACY_INSIGHT_NAV_IDS.includes(nav)) {
      return { nav: 'insight', insightTab: nav }
    }
    return { nav: resolveHumanNavToActive(nav) }
  }

  function guardReviewerNav(nav) {
    if (!utils.isReviewerUrl()) return nav
    const canonical = utils.canonicalNav(nav)
    if (REVIEWER_BLOCKED_NAV.has(canonical)) return 'inbox'
    return canonical
  }

  function syncNavUrl() {
    if (typeof window === 'undefined') return
    const url = new URL(window.location.href)
    const urlNav = activeNavToUrlParam(activeNav.value)
    if (urlNav && urlNav !== 'ask') {
      url.searchParams.set('nav', urlNav)
    } else if (urlNav === 'ask') {
      url.searchParams.set('nav', 'ask')
    } else {
      url.searchParams.delete('nav')
    }
    if (activeNav.value === 'produce') {
      url.searchParams.set('tab', produceTab.value || 'studio')
    } else if (activeNav.value === 'inbox') {
      url.searchParams.set('tab', inboxTab.value || 'decisions')
    } else if (activeNav.value === 'insight') {
      url.searchParams.set('tab', insightTab.value || 'overview')
    } else {
      url.searchParams.delete('tab')
    }
    if (focusChapter.value != null) {
      url.searchParams.set('chapter', String(focusChapter.value))
    } else {
      url.searchParams.delete('chapter')
    }
    if (focusDecisionId.value) {
      url.searchParams.set('decision', focusDecisionId.value)
    } else {
      url.searchParams.delete('decision')
    }
    if (focusWizard.value) {
      url.searchParams.set('wizard', '1')
    } else {
      url.searchParams.delete('wizard')
    }
    if (focusWizardStep.value) {
      url.searchParams.set('step', focusWizardStep.value)
    } else {
      url.searchParams.delete('step')
    }
    if (focusWizardDone.value && focusWizardDone.value.length) {
      url.searchParams.set('done', focusWizardDone.value.join(','))
    } else {
      url.searchParams.delete('done')
    }
    const encodedNotes = utils.encodeWizardNotes(focusWizardNotes.value)
    if (encodedNotes) {
      url.searchParams.set('notes', encodedNotes)
    } else {
      url.searchParams.delete('notes')
    }
    if (activeNav.value === 'creator') {
      const ws = focusCreatorWorkspace.value
      if (ws && ws !== 'write' && CREATOR_WORKSPACE_IDS.includes(ws)) {
        url.searchParams.set('workspace', ws)
      } else {
        url.searchParams.delete('workspace')
      }
    } else {
      url.searchParams.delete('workspace')
    }
    utils.preserveRoleParams(url)
    window.history.replaceState(window.history.state, '', url.toString())
  }

  function navigateTo(nav, opts = {}) {
    const target = resolveNavTarget(nav)
    const resolved = guardReviewerNav(target.nav)
    activeNav.value = VALID_NAV.includes(nav) || nav === 'write' || nav === 'creator'
      ? resolved
      : (utils.isReviewerUrl() ? 'inbox' : 'ask')
    if (opts.tab) {
      if (activeNav.value === 'produce' && PRODUCE_TAB_IDS.includes(opts.tab)) {
        produceTab.value = opts.tab
      }
      if (activeNav.value === 'inbox' && INBOX_TAB_IDS.includes(opts.tab)) {
        inboxTab.value = opts.tab
      }
      if (activeNav.value === 'insight' && INSIGHT_TAB_IDS.includes(opts.tab)) {
        insightTab.value = opts.tab
      }
    } else if (LEGACY_PRODUCE_NAV_IDS.includes(nav)) {
      produceTab.value = nav
    } else if (LEGACY_INBOX_NAV_IDS.includes(nav)) {
      inboxTab.value = nav
    } else if (LEGACY_INSIGHT_NAV_IDS.includes(nav)) {
      insightTab.value = nav
    }
    if (opts.clearFocus) {
      focusChapter.value = null
      focusDecisionId.value = null
      focusWizardStep.value = null
      focusWizardDone.value = []
      focusWizardNotes.value = {}
      focusCreatorWorkspace.value = null
    } else {
      if (opts.chapter !== undefined) focusChapter.value = opts.chapter
      if (opts.decisionId !== undefined) focusDecisionId.value = opts.decisionId
      if (opts.wizardStep !== undefined) focusWizardStep.value = opts.wizardStep
      if (opts.wizardDone !== undefined) focusWizardDone.value = opts.wizardDone || []
      if (opts.wizardNotes !== undefined) focusWizardNotes.value = opts.wizardNotes || {}
    }
    if (opts.wizard !== undefined) focusWizard.value = Boolean(opts.wizard)
    if (opts.wizardStep) focusWizard.value = true
    if (opts.wizardDone?.length) focusWizard.value = true
    if (opts.wizardNotes && Object.keys(opts.wizardNotes).length) focusWizard.value = true
    if (opts.workspace !== undefined) {
      focusCreatorWorkspace.value = utils.normalizeCreatorWorkspace(opts.workspace)
    }
    syncNavUrl()
  }

  function setProduceTab(tab) {
    if (!PRODUCE_TAB_IDS.includes(tab)) return
    produceTab.value = tab
    activeNav.value = 'produce'
    syncNavUrl()
  }

  function setInboxTab(tab) {
    if (!INBOX_TAB_IDS.includes(tab)) return
    inboxTab.value = tab
    activeNav.value = 'inbox'
    syncNavUrl()
  }

  function setInsightTab(tab) {
    if (!INSIGHT_TAB_IDS.includes(tab)) return
    insightTab.value = tab
    activeNav.value = 'insight'
    syncNavUrl()
  }

  function setCreatorWorkspace(tab) {
    focusCreatorWorkspace.value = utils.normalizeCreatorWorkspace(tab)
    syncNavUrl()
  }

  function setWizardDeepLink(open, wizardStep, wizardDone, wizardNotes) {
    focusWizard.value = Boolean(open)
    if (wizardStep !== undefined) {
      focusWizardStep.value = wizardStep || null
    }
    if (wizardDone !== undefined) {
      focusWizardDone.value = wizardDone || []
    }
    if (wizardNotes !== undefined) {
      focusWizardNotes.value = wizardNotes || {}
    }
    syncNavUrl()
  }

  function buildWizardShareUrl(completedStepIds, wizardStep, stepNotes) {
    if (typeof window === 'undefined') return ''
    const url = new URL(window.location.href)
    url.searchParams.set('nav', 'write')
    url.searchParams.set('wizard', '1')
    const done = (completedStepIds || []).filter(Boolean)
    if (done.length) {
      url.searchParams.set('done', done.join(','))
    } else {
      url.searchParams.delete('done')
    }
    if (wizardStep) {
      url.searchParams.set('step', wizardStep)
    }
    const encodedNotes = utils.encodeWizardNotes(stepNotes)
    if (encodedNotes) {
      url.searchParams.set('notes', encodedNotes)
    } else {
      url.searchParams.delete('notes')
    }
    return url.toString()
  }

  function clearDecisionFocus() {
    focusChapter.value = null
    focusDecisionId.value = null
    syncNavUrl()
  }

  function syncNavFromBrowserUrl() {
    const raw = utils.readRawNavFromUrl()
    activeNav.value = utils.readNavFromUrl()
    produceTab.value = utils.readProduceTab(raw)
    inboxTab.value = utils.readInboxTab(raw)
    insightTab.value = utils.readInsightTab(raw)
    focusChapter.value = utils.readChapterFromUrl()
    focusDecisionId.value = utils.readDecisionFromUrl()
    focusWizard.value = utils.readWizardFromUrl()
    focusWizardStep.value = utils.readWizardStepFromUrl()
    focusWizardDone.value = utils.readWizardDoneFromUrl()
    focusWizardNotes.value = utils.readWizardNotesFromUrl()
    focusCreatorWorkspace.value = utils.readCreatorWorkspaceFromUrl()
  }

  function isProduceNav(nav) {
    return nav === 'produce' || LEGACY_PRODUCE_NAV_IDS.includes(nav)
  }

  function isInboxNav(nav) {
    return nav === 'inbox' || LEGACY_INBOX_NAV_IDS.includes(nav)
  }

  function isInsightNav(nav) {
    return nav === 'insight' || LEGACY_INSIGHT_NAV_IDS.includes(nav)
  }

  function isWriteNav(nav) {
    return nav === 'creator' || nav === 'write'
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('popstate', () => {
      syncNavFromBrowserUrl()
    })
  }

  return {
    activeNav,
    produceTab,
    inboxTab,
    insightTab,
    focusChapter,
    focusDecisionId,
    focusWizard,
    focusWizardStep,
    focusWizardDone,
    focusWizardNotes,
    focusCreatorWorkspace,
    navigateTo,
    setProduceTab,
    setInboxTab,
    setInsightTab,
    setCreatorWorkspace,
    syncNavFromBrowserUrl,
    syncNavUrl,
    isProduceNav,
    isInboxNav,
    isInsightNav,
    isWriteNav,
    setWizardDeepLink,
    buildWizardShareUrl,
    clearDecisionFocus,
  }
})