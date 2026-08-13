/**
 * 今日页次要链接：主 CTA 已覆盖的事项不再重复，其余待办以一行链接展示。
 */

/**
 * @param {Array<{ id: string, label: string, value: number, nav: string, tab?: string }>} todoCards
 * @param {{ id?: string } | null | undefined} primaryAction
 */
export function buildTodaySecondaryLinks(todoCards, primaryAction) {
  const primaryId = primaryAction?.id;
  return (todoCards || [])
    .filter((card) => card.value > 0 && card.id !== primaryId)
    .map((card) => ({
      id: card.id,
      nav: card.nav,
      tab: card.tab,
      label: formatTodaySecondaryLabel(card),
    }));
}

/** @param {{ id: string, label: string, value: number }} card */
function formatTodaySecondaryLabel(card) {
  const n = card.value;
  const map = {
    decisions: `还有 ${n} 条待决策`,
    ripples: `还有 ${n} 条一致性变更`,
    p0: `还有 ${n} 条质检 P0`,
    alerts: `还有 ${n} 处脉络预警`,
  };
  return map[card.id] || `还有 ${n} 条${card.label}`;
}
