/** 主顶栏上下文标题（侧栏品牌见 config/brand.js） */
export const NAV_CONTEXT_TITLES = {
  ask: '聊聊',
  write: '书桌',
  creator: '书桌',
  library: '书架',
  more: '工具箱',
  today: '今日',
  produce: '生产',
  inbox: '待办',
  insight: '洞察',
  'cascade-runs': '级联',
  settings: '设置',
};

export function resolveNavContextTitle(activeNav, { isReviewer = false } = {}) {
  if (isReviewer) return '审阅视图';
  return NAV_CONTEXT_TITLES[activeNav] || '灵文';
}
