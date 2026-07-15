/**
 * Human-first sidebar + creation_mode trimming (frontend-ia-v1.md).
 *
 * companion — 隐藏「更多」内的生产入口（生产链接不出现在 More 页）
 * advance   — 全开
 * studio    — 隐藏「书桌」（工厂用户从工具箱/生产进）
 */
import { HUMAN_FIRST_NAV_GROUPS } from './humanFirstNav.js';
import { REVIEWER_NAV_GROUPS } from './dashboardNav.js';

/** @type {Record<string, string[]>} */
export const MODE_NAV_ITEM_IDS = {
  companion: ['ask', 'write', 'library', 'more', 'settings'],
  advance: ['ask', 'write', 'library', 'more', 'settings'],
  studio: ['ask', 'library', 'more', 'settings'],
};

/** 「更多」页内链接 id — 按模式裁剪 */
/** @type {Record<string, string[]>} */
export const MODE_MORE_LINK_IDS = {
  companion: ['today', 'inbox', 'insight'],
  advance: ['today', 'produce', 'inbox', 'insight', 'cascade-runs'],
  studio: ['today', 'produce', 'inbox', 'insight', 'cascade-runs'],
};

const PRODUCE_NAV_IDS = new Set(['produce', 'studio', 'chapters', 'workflows']);
const INBOX_NAV_IDS = new Set(['inbox', 'decisions', 'ripples']);
const INSIGHT_NAV_IDS = new Set(['insight', 'overview', 'analytics']);
const WRITE_NAV_IDS = new Set(['write', 'creator']);

/**
 * @param {string | null | undefined} mode
 * @returns {'companion' | 'advance' | 'studio'}
 */
export function resolveNavCreationMode(mode) {
  if (mode === 'advance' || mode === 'studio') return mode;
  return 'companion';
}

/**
 * @param {string} navId
 * @param {string | null | undefined} creationMode
 */
export function isNavItemAllowedForMode(navId, creationMode) {
  const mode = resolveNavCreationMode(creationMode);
  const allowed = new Set(MODE_NAV_ITEM_IDS[mode]);
  if (allowed.has(navId)) return true;
  if (WRITE_NAV_IDS.has(navId)) return allowed.has('write');
  if (navId === 'creator') return allowed.has('write');
  if (PRODUCE_NAV_IDS.has(navId)) return MODE_MORE_LINK_IDS[mode]?.includes('produce');
  if (INBOX_NAV_IDS.has(navId)) return MODE_MORE_LINK_IDS[mode]?.includes('inbox');
  if (INSIGHT_NAV_IDS.has(navId)) return MODE_MORE_LINK_IDS[mode]?.includes('insight');
  if (navId === 'today') return MODE_MORE_LINK_IDS[mode]?.includes('today');
  if (navId === 'cascade-runs') return MODE_MORE_LINK_IDS[mode]?.includes('cascade-runs');
  if (navId === 'settings') return MODE_MORE_LINK_IDS[mode]?.includes('settings');
  if (navId === 'ask' || navId === 'library' || navId === 'more') return allowed.has(navId);
  return allowed.has(navId);
}

/**
 * @param {string | null | undefined} creationMode
 * @param {{ isReviewer?: boolean }} [options]
 */
export function buildVisibleNavGroups(creationMode, options = {}) {
  if (options.isReviewer) {
    return REVIEWER_NAV_GROUPS.map((group) => ({
      ...group,
      hideGroupLabel: true,
      showDivider: false,
      items: group.items,
    }));
  }

  const mode = resolveNavCreationMode(creationMode);
  const allowed = new Set(MODE_NAV_ITEM_IDS[mode]);

  return HUMAN_FIRST_NAV_GROUPS
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => allowed.has(item.id)),
    }))
    .filter((group) => group.items.length > 0);
}

/**
 * @param {string | null | undefined} creationMode
 */
export function buildMorePageLinks(creationMode) {
  const mode = resolveNavCreationMode(creationMode);
  const ids = MODE_MORE_LINK_IDS[mode] || MODE_MORE_LINK_IDS.companion;
  const defs = {
    today: { id: 'today', label: '今日概览', desc: '任务、健康度与快捷入口', mark: '今', nav: 'today' },
    produce: { id: 'produce', label: '生产', desc: '控制台、章节与工作流', mark: '产', nav: 'produce', tab: 'studio' },
    inbox: { id: 'inbox', label: '待办', desc: '待决策与一致性审阅', mark: '办', nav: 'inbox', tab: 'decisions' },
    insight: { id: 'insight', label: '洞察', desc: '追读力与分析', mark: '察', nav: 'insight', tab: 'overview' },
    'cascade-runs': { id: 'cascade-runs', label: '级联', desc: '级联运行记录', mark: '联', nav: 'cascade-runs' },
    settings: { id: 'settings', label: '设置', desc: '运行状态与界面偏好', mark: '设', nav: 'settings' },
  };
  return ids.map((id) => defs[id]).filter(Boolean);
}

/**
 * @param {string} activeNav
 * @param {string | null | undefined} creationMode
 * @param {{ allowCreatorWizard?: boolean }} [options]
 * @returns {string | null}
 */
export function suggestNavFallback(activeNav, creationMode, options = {}) {
  const mode = resolveNavCreationMode(creationMode);
  if (WRITE_NAV_IDS.has(activeNav) && mode === 'studio') {
    return options.allowCreatorWizard ? null : 'produce';
  }
  if (PRODUCE_NAV_IDS.has(activeNav) && mode === 'companion') {
    return 'write';
  }
  if (activeNav === 'creator' && mode === 'studio') {
    return options.allowCreatorWizard ? null : 'produce';
  }
  if (!isNavItemAllowedForMode(activeNav, creationMode) && !['ask', 'today'].includes(activeNav)) {
    return mode === 'studio' ? 'ask' : 'ask';
  }
  return null;
}
