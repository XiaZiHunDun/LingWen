/**
 * useNavUrlUtils — URL 解析/编码/规范化 helpers（从 useNavStore.js 拆出）
 *
 * Phase 63.1: 17 helpers 独立 composable，可独立测试 + 复用。
 * 不依赖 Pinia store 状态，纯函数（除 `window` 引用外）。
 */

import {
  LEGACY_INBOX_NAV_IDS,
  LEGACY_INSIGHT_NAV_IDS,
  LEGACY_PRODUCE_NAV_IDS,
} from '../config/dashboardNav.js'
import {
  PRODUCE_TAB_IDS,
  INBOX_TAB_IDS,
  INSIGHT_TAB_IDS,
  CREATOR_WORKSPACE_IDS,
  VALID_NAV,
  REVIEWER_BLOCKED_NAV,
} from './navConstants'

export function useNavUrlUtils() {
  function canonicalNav(nav: string): string {
    if (!nav) return 'ask'
    if (nav === 'write' || nav === 'creator') return 'creator'
    if (LEGACY_PRODUCE_NAV_IDS.includes(nav)) return 'produce'
    if (LEGACY_INBOX_NAV_IDS.includes(nav)) return 'inbox'
    if (LEGACY_INSIGHT_NAV_IDS.includes(nav)) return 'insight'
    return nav
  }

  function readRawNavFromUrl(): string | null {
    if (typeof window === 'undefined') return null
    return new URLSearchParams(window.location.search).get('nav')
  }

  function isReviewerUrl(): boolean {
    if (typeof window === 'undefined') return false
    const params = new URLSearchParams(window.location.search)
    return params.get('role') === 'reviewer' || params.get('review') === '1'
  }

  function readProduceTab(rawNav: string | null): string {
    if (typeof window === 'undefined') return 'studio'
    const tab = new URLSearchParams(window.location.search).get('tab')
    if (tab && PRODUCE_TAB_IDS.includes(tab)) return tab
    if (rawNav && LEGACY_PRODUCE_NAV_IDS.includes(rawNav)) return rawNav
    return 'studio'
  }

  function readInboxTab(rawNav: string | null): string {
    if (typeof window === 'undefined') return 'decisions'
    const tab = new URLSearchParams(window.location.search).get('tab')
    if (tab && INBOX_TAB_IDS.includes(tab)) return tab
    if (rawNav && LEGACY_INBOX_NAV_IDS.includes(rawNav)) return rawNav
    return 'decisions'
  }

  function readInsightTab(rawNav: string | null): string {
    if (typeof window === 'undefined') return 'overview'
    const tab = new URLSearchParams(window.location.search).get('tab')
    if (tab && INSIGHT_TAB_IDS.includes(tab)) return tab
    if (rawNav && LEGACY_INSIGHT_NAV_IDS.includes(rawNav)) return rawNav
    return 'overview'
  }

  function readCreatorWorkspaceFromUrl(): string | null {
    if (typeof window === 'undefined') return null
    const ws = new URLSearchParams(window.location.search).get('workspace')
    if (ws && CREATOR_WORKSPACE_IDS.includes(ws) && ws !== 'write') return ws
    return null
  }

  function normalizeCreatorWorkspace(tab: string | null | undefined): string | null {
    if (!tab || tab === 'write') return null
    return CREATOR_WORKSPACE_IDS.includes(tab) ? tab : null
  }

  function readNavFromUrl(): string | null {
    if (typeof window === 'undefined') return 'ask'
    const raw = readRawNavFromUrl()
    if (!raw) return isReviewerUrl() ? 'inbox' : null
    if (!VALID_NAV.includes(raw)) return isReviewerUrl() ? 'inbox' : 'ask'
    const canonical = canonicalNav(raw)
    if (isReviewerUrl() && REVIEWER_BLOCKED_NAV.has(canonical)) {
      return 'inbox'
    }
    if (isReviewerUrl() && REVIEWER_BLOCKED_NAV.has(raw)) {
      return 'inbox'
    }
    return canonical
  }

  function readChapterFromUrl(): number | null {
    if (typeof window === 'undefined') return null
    const raw = new URLSearchParams(window.location.search).get('chapter')
    if (raw == null || raw === '') return null
    const n = Number(raw)
    return Number.isFinite(n) && n >= 1 ? n : null
  }

  function readDecisionFromUrl(): string | null {
    if (typeof window === 'undefined') return null
    const id = new URLSearchParams(window.location.search).get('decision')
    return id && id.trim() ? id.trim() : null
  }

  function encodeWizardNotes(notes: Record<string, unknown> | null | undefined): string | null {
    const filtered = Object.fromEntries(
      Object.entries(notes || {}).filter(([, value]) => String(value).trim()),
    )
    if (!Object.keys(filtered).length) return null
    return btoa(unescape(encodeURIComponent(JSON.stringify(filtered))))
  }

  function readWizardNotesFromUrl(): Record<string, unknown> {
    if (typeof window === 'undefined') return {}
    const raw = new URLSearchParams(window.location.search).get('notes')
    if (!raw) return {}
    try {
      const json = decodeURIComponent(escape(atob(raw)))
      const parsed = JSON.parse(json)
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch {
      return {}
    }
  }

  function readWizardFromUrl(): boolean {
    if (typeof window === 'undefined') return false
    const params = new URLSearchParams(window.location.search)
    return (
      params.get('wizard') === '1'
      || Boolean(params.get('step'))
      || Boolean(params.get('done'))
      || Boolean(params.get('notes'))
    )
  }

  function readWizardStepFromUrl(): string | null {
    if (typeof window === 'undefined') return null
    const step = new URLSearchParams(window.location.search).get('step')
    return step && step.trim() ? step.trim() : null
  }

  function readWizardDoneFromUrl(): string[] {
    if (typeof window === 'undefined') return []
    const raw = new URLSearchParams(window.location.search).get('done')
    if (!raw || !raw.trim()) return []
    return raw.split(',').map((s) => s.trim()).filter(Boolean)
  }

  function preserveRoleParams(url: URL): void {
    if (typeof window === 'undefined') return
    const current = new URL(window.location.href)
    const role = current.searchParams.get('role')
    const review = current.searchParams.get('review')
    if (role) {
      url.searchParams.set('role', role)
    } else {
      url.searchParams.delete('role')
    }
    if (!role && review === '1') {
      url.searchParams.set('review', '1')
    } else {
      url.searchParams.delete('review')
    }
  }

  return {
    canonicalNav,
    readRawNavFromUrl,
    isReviewerUrl,
    readProduceTab,
    readInboxTab,
    readInsightTab,
    readCreatorWorkspaceFromUrl,
    normalizeCreatorWorkspace,
    readNavFromUrl,
    readChapterFromUrl,
    readDecisionFromUrl,
    encodeWizardNotes,
    readWizardNotesFromUrl,
    readWizardFromUrl,
    readWizardStepFromUrl,
    readWizardDoneFromUrl,
    preserveRoleParams,
  }
}
