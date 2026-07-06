/**
 * Human-first L1 navigation (frontend-ia-v1.md).
 * User-facing labels; internal write → CreatorPage via nav alias.
 */

/** @typedef {{ id: string, label: string, icon: string }} HumanNavItem */

export const HUMAN_FIRST_NAV_GROUPS = [
  {
    id: 'primary',
    label: '',
    hideGroupLabel: true,
    showDivider: false,
    items: [
      { id: 'ask', label: '聊聊' },
      { id: 'write', label: '书桌' },
      { id: 'library', label: '书架' },
    ],
  },
  {
    id: 'more_group',
    label: '',
    hideGroupLabel: true,
    showDivider: true,
    items: [
      { id: 'more', label: '工具箱' },
      { id: 'settings', label: '设置' },
    ],
  },
];

export const HUMAN_FIRST_NAV_IDS = HUMAN_FIRST_NAV_GROUPS.flatMap((g) => g.items.map((i) => i.id));

/** Nav id shown in sidebar → active page key */
export const NAV_WRITE_ALIASES = new Set(['write', 'creator']);

/** URL / sidebar id → internal activeNav for App.vue */
export function resolveHumanNavToActive(navId) {
  if (NAV_WRITE_ALIASES.has(navId)) return 'creator';
  return navId;
}

/** activeNav → URL nav param (user-facing) */
export function activeNavToUrlParam(activeNav) {
  if (activeNav === 'creator') return 'write';
  return activeNav;
}

/** Whether sidebar item should highlight */
export function isHumanNavItemActive(itemId, activeNav) {
  if (itemId === 'write') return activeNav === 'creator';
  return activeNav === itemId;
}
