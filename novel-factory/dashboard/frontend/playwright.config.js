// playwright.config.js — Phase 8.45.3 / Phase 9.48 F37 / Phase 9.65 F56
// Playwright opt-in smoke (vitest remains primary gate).
// Local smoke: pnpm e2e:smoke (vite only, app-root.spec.js)
// Live backend: LINGWEN_E2E_LIVE=1 pnpm e2e:live (vite + dashboard/e2e_entry.py)

import { defineConfig, devices } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const NOVEL_FACTORY_ROOT = path.resolve(__dirname, '../..')

const liveE2E = process.env.LINGWEN_E2E_LIVE === '1'

const viteServer = {
  command: 'pnpm dev --port 5173 --strictPort',
  url: 'http://localhost:5173',
  reuseExistingServer: !process.env.CI,
  timeout: 120_000,
}

const dashboardServer = {
  command: 'python dashboard/e2e_entry.py',
  cwd: NOVEL_FACTORY_ROOT,
  url: 'http://localhost:8765/api/health',
  reuseExistingServer: !process.env.CI,
  timeout: 120_000,
}

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
    {
      name: 'smoke',
      testMatch: /app-root\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'live-backend',
      testMatch: /(ripples-audit|decisions-resolve)\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: liveE2E ? [dashboardServer, viteServer] : viteServer,
})
