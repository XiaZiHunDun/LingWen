import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.27 — WebSocket 断线 indicator
 * 验证 SidebarCostBanner 组件在 useWorkflowSocket.connected=false 时
 * 渲染黄色 ⚠️ "实时同步已断开" 提示 banner。
 *
 * 跟 sidebar_cost_banner.spec.js (Phase 8.11+) 同模式: page.route mock +
 * 断言 .ws-disconnected-banner visible.
 *
 * 当前 Playwright runner 未装 (跟 Phase 7.6/8.7/8.8/8.13/8.17 一致),
 * 作为契约文档存在.
 *
 * 契约:
 *   - connected=false + hasMounted=true → 渲染 .ws-disconnected-banner
 *   - connected=true → banner NOT visible (即使 hasMounted=true)
 *   - hasMounted=false (mount 后 200ms 内) → banner NOT visible (避免 flash)
 *   - role="alert" + aria-live="assertive" (跟 a11y 现有 banner 一致)
 *   - 含中文 "实时同步已断开" + "成本数据可能过期" 提示
 *   - 黄底色 (#fff3cd) + pulse animation (1.5s ease-in-out infinite)
 *
 * 注: connected 状态由 useWorkflowSocket 管理 (Phase 6.4 + 8.11 singleton),
 * SidebarCostBanner 通过共享 composable 读 connected ref, 0 改 WS 逻辑.
 */

test.describe('Sidebar WebSocket Disconnected Indicator (Phase 8.27)', () => {
  test.setTimeout(30000)

  test('shows disconnected banner when WebSocket is closed', async ({ page }) => {
    // Mock /api/workflows/active 返 cost fixture (banner 需要 hasCost=true)
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 5,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 5,
          total_cost_usd: 0.045,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.025,
            chapter_review: 0.020,
          },
        }),
      })
    })

    // 阻止 WebSocket 建立 (closed state 模拟)
    await page.route('**/api/ws/workflows', async (route) => {
      await route.abort()
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // 等待 hasMounted gate (200ms) 之后, connected 仍 false → banner 可见
    const banner = page.getByTestId('ws-disconnected-banner')
    await expect(banner).toBeVisible({ timeout: 2000 })
    await expect(banner).toContainText('实时同步已断开')
    await expect(banner).toContainText('成本数据可能过期')
  })

  test('hides disconnected banner when WebSocket is connected', async ({ page }) => {
    // Mock /api/workflows/active 返 cost fixture
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 5,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 5,
          total_cost_usd: 0.045,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.025,
            chapter_review: 0.020,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // WebSocket 正常建立 → connected=true → banner NOT visible
    const banner = page.getByTestId('ws-disconnected-banner')
    await expect(banner).not.toBeVisible({ timeout: 2000 })
  })
})
