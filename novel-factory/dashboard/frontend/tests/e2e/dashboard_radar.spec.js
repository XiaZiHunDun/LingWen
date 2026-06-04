import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 7.6 — Dashboard S1-S8 评分雷达图
 * 验证 WorkflowStatus 组件在 active workflow 含 score_data 时渲染雷达图
 */

test.describe('Dashboard Score Radar (Phase 7.6)', () => {
  test.setTimeout(30000)

  test('radar chart renders 8 S1-S8 dimensions when score_data present', async ({ page }) => {
    // Mock /api/workflows/active 返 score_data
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_active: true,
          workflow_name: 'novel_writing',
          completed: 7,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 7,
          pending_decisions: [],
          executions: { polish_merge: 'completed' },
          score_data: {
            polish_merge: {
              scores_a: { S1: 8, S2: 7, S3: 9, S4: 8, S5: 7, S6: 8, S7: 9, S8: 8 },
              scores_b: { S1: 5, S2: 5, S3: 5, S4: 5, S5: 5, S6: 5, S7: 5, S8: 5 },
              scores_total_a: 8.0,
              scores_total_b: 5.0,
              scores_delta: 3.0,
              winner: 'polish_emotional_pacing',
              label_a: 'polish_emotional_pacing',
              label_b: 'polish_ai_trace_removal',
              fallback: null,
            },
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // 雷达图组件应可见
    const radar = page.locator('.score-radar-chart')
    await expect(radar).toBeVisible({ timeout: 10000 })

    // 8 维 indicator (S1-S8) 应渲染 (ECharts 会渲染 text 元素)
    const indicators = page.locator('.score-radar-chart canvas')
    await expect(indicators.first()).toBeVisible({ timeout: 5000 })

    // winner badge 可见
    const winnerBadge = page.locator('.winner-badge:has-text("polish_emotional_pacing")')
    await expect(winnerBadge).toBeVisible()
  })

  test('fallback warning shown when score_data has fallback reason', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_active: true,
          workflow_name: 'novel_writing',
          completed: 7, failed: 0, paused: false, paused_nodes: [],
          node_count: 7, steps: 7, pending_decisions: [],
          executions: { polish_merge: 'completed' },
          score_data: {
            polish_merge: {
              scores_a: {}, scores_b: {},
              scores_total_a: 0, scores_total_b: 0, scores_delta: 0,
              winner: '', label_a: 'A', label_b: 'B', fallback: 'llm_fail',
            },
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // 警告横幅应可见
    const warning = page.locator('.score-radar-fallback-warning:has-text("LLM 评分未生效")')
    await expect(warning).toBeVisible({ timeout: 10000 })
  })
})
