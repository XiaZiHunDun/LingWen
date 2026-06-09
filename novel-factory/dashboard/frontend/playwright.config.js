// playwright.config.js — Phase 8.45.3
// Playwright config (0 browser download, 0 CI integration).
// dev opt-in: npx playwright install chromium 装 browser 后跑 pnpm e2e:smoke
// vitest 走 dashboard-frontend-ci.yml 仍 vitest primary gate, Playwright 留
// manual + future CI integration (Phase 8.46+ followup).

import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e-smoke',
  fullyParallel: false, // Phase 8.45.3 1 spec 单 thread 简化
  forbidOnly: !!process.env.CI,
  retries: 0, // 0 retry 简单 smoke
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173', // 跟 vite dev server default port
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // 0 webServer 配, dev 手动启 vite (`pnpm dev`), smoke 走 http://localhost:5173
})
