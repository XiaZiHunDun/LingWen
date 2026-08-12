// tests/helpers/by-testid.ts — Phase 8.35 helper
// 用法: wrapper.find(byTestid('x')) 等价 wrapper.find('[data-testid="x"]')
// 形态: simple string (主公决策 Option A 2026-06-08), 0 返 object wrapper.
// 0 escape: raw passthrough, 调用方负责 id 拼写合法 (kebab-case 推荐).

export function byTestid(id: string): string {
  return `[data-testid="${id}"]`
}
