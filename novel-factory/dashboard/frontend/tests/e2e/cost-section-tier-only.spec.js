// Phase 8.14: hasCost gate tier 维度补全 ceremonial e2e spec
// 3 test cases: tier-only visible / neither hidden / both visible (sanity)
//
// 跟 Phase 7.6/8.7/8.8/8.11/8.13/8.15 ceremonial specs 同模式:
// Playwright runner 未装, 作为契约文档存在 (header note).
// Mock 走 page.route('**/api/workflows/active') 模式跟 7 specs 一致.

import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'

const ACTIVE_WORKFLOW = (cost_by_scenario, cost_by_tier) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 5,
  failed: 0,
  node_count: 7,
  steps: 12,
  cost_by_scenario,
  cost_by_tier,
  total_cost_usd: 0.05,
})

test.describe('Phase 8.14: WorkflowStatus hasCost gate (scenario + tier OR)', () => {
  test('shows_cost_section_when_only_tier_data_present', async ({ page }) => {
    // Phase 8.14 fix: tier-only 数据时 cost section 必须 visible
    // 旧 hasCost 仅查 costByScenario → RED 状态 (本测试断言)
    await page.route('**/api/workflows/active', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_WORKFLOW({}, { haiku: 0.05 })),
      })
    })
    await page.goto(`${BASE_URL}/workflows`)
    await expect(page.locator('.cost-section')).toBeVisible()
  })

  test('hides_cost_section_when_neither_present', async ({ page }) => {
    // 旧行为保: 双方都空 → cost section hidden
    await page.route('**/api/workflows/active', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_WORKFLOW({}, {})),
      })
    })
    await page.goto(`${BASE_URL}/workflows`)
    await expect(page.locator('.cost-section')).toBeHidden()
  })

  test('shows_cost_section_when_both_present', async ({ page }) => {
    // Sanity: 双方有值 → visible (Phase 8.13 path 不破)
    await page.route('**/api/workflows/active', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          ACTIVE_WORKFLOW(
            { chapter_writing: 0.03 },
            { haiku: 0.01, sonnet: 0.02 },
          ),
        ),
      })
    })
    await page.goto(`${BASE_URL}/workflows`)
    await expect(page.locator('.cost-section')).toBeVisible()
  })
})
