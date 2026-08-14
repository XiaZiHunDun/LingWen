/**
 * useCreatorPage 子模块聚合入口 — Phase 21
 *
 * 把 useCreatorPage.js 509 行编排型实现 + chrome 上下文抽取：
 * - useCreatorPageChrome (页面 chrome 上下文聚合 + workspaceTabBadges 合并)
 *
 * 注意: useCreatorPage 主体是编排型（组合 9 个子 hub），
 *       本子模块仅处理可独立抽取的 chrome 聚合逻辑。
 */
export { useCreatorPageChrome } from './useCreatorPageChrome';