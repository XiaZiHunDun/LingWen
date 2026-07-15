/**
 * Phase A/B product IA — grouped sidebar.
 * Phase B: single door for 生产 (produce) and 待办 (inbox).
 */

export const PRODUCE_TABS = [
  { id: 'studio', label: '控制台', icon: '🏭' },
  { id: 'chapters', label: '章节', icon: '📖' },
  { id: 'workflows', label: '工作流', icon: '🔀' },
];

export const INBOX_TABS = [
  { id: 'decisions', label: '待决策', icon: '⚡' },
  { id: 'ripples', label: '一致性', icon: '🌀' },
];

export const INSIGHT_TABS = [
  { id: 'overview', label: '追读力', icon: '📊' },
  { id: 'analytics', label: '分析', icon: '📈' },
];

export const DASHBOARD_NAV_GROUPS = [
  {
    id: 'hub',
    label: '今天',
    items: [{ id: 'today', label: '今日', icon: '🏠' }],
  },
  {
    id: 'write',
    label: '写作',
    items: [{ id: 'creator', label: '创作', icon: '✍️' }],
  },
  {
    id: 'produce',
    label: '生产',
    items: [{ id: 'produce', label: '生产', icon: '🏭' }],
  },
  {
    id: 'inbox',
    label: '待办',
    items: [{ id: 'inbox', label: '待办', icon: '📥' }],
  },
  {
    id: 'insight',
    label: '洞察',
    items: [{ id: 'insight', label: '洞察', icon: '📊' }],
  },
  {
    id: 'system',
    label: '系统',
    items: [
      { id: 'cascade-runs', label: '级联', icon: '🔁' },
      { id: 'settings', label: '设置', icon: '⚙️' },
    ],
  },
];

export const DASHBOARD_NAV_IDS = DASHBOARD_NAV_GROUPS.flatMap((g) => g.items.map((i) => i.id));

export const LEGACY_PRODUCE_NAV_IDS = ['studio', 'chapters', 'workflows'];
export const LEGACY_INBOX_NAV_IDS = ['decisions', 'ripples'];
export const LEGACY_INSIGHT_NAV_IDS = ['overview', 'analytics'];

/** Sidebar groups visible to external reviewers (?role=reviewer). */
export const REVIEWER_NAV_GROUPS = [
  {
    id: 'hub',
    label: '今天',
    items: [{ id: 'today', label: '今日', icon: '🏠' }],
  },
  {
    id: 'inbox',
    label: '待办',
    items: [{ id: 'inbox', label: '待办', icon: '📥' }],
  },
  {
    id: 'insight',
    label: '洞察',
    items: [{ id: 'insight', label: '洞察', icon: '📊' }],
  },
];
