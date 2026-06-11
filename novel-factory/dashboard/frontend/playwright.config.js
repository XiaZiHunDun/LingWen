// playwright.config.js — Phase 8.45.3 / Phase 9.31 F15 / Phase 9.48 F37
// Playwright opt-in smoke (vitest remains primary gate).
// Phase 9.48 F37: CI via dashboard-e2e-smoke.yml (workflow_dispatch / label e2e-smoke).
// Local: pnpm e2e:smoke (auto-starts vite when no server on :5173).

import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e-smoke',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'pnpm dev --port 5173 --strictPort',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
