/**
 * navConstants — 6 nav-related constants shared between useNavStore and useNavUrlUtils
 *
 * Phase 64.1: 从 useNavStore.js + useNavUrlUtils.ts 抽取 6 个重复 constants。
 * 单一 source of truth，杜绝两份定义 drift。
 */

import { PRODUCE_TABS, INBOX_TABS, INSIGHT_TABS } from '../config/dashboardNav.js'

export const PRODUCE_TAB_IDS: string[] = PRODUCE_TABS.map((t) => t.id)
export const INBOX_TAB_IDS: string[] = INBOX_TABS.map((t) => t.id)
export const INSIGHT_TAB_IDS: string[] = INSIGHT_TABS.map((t) => t.id)

export const CREATOR_WORKSPACE_IDS: string[] = ['write', 'pulse', 'settings']

export const VALID_NAV: string[] = [
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

export const REVIEWER_BLOCKED_NAV: Set<string> = new Set([
  'write', 'creator', 'produce', 'library', 'more', 'settings', 'cascade-runs',
  'studio', 'chapters', 'workflows',
])
