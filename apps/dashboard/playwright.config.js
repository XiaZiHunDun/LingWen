// playwright.config.js — Phase 8.45.3 / Phase 9.48 F37 / Phase 9.65 F56
// Playwright opt-in smoke (vitest remains primary gate).
// Local smoke: pnpm e2e:smoke (vite only, app-root.spec.js)
// Live backend: LINGWEN_E2E_LIVE=1 pnpm e2e:live (vite + dashboard/e2e_entry.py)

import { defineConfig, devices } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const NOVEL_FACTORY_ROOT = path.resolve(__dirname, '../..')

import { QUARANTINE_ONLY } from './tests/e2e-smoke/helpers/quarantine.js'

const liveE2E = process.env.LINGWEN_E2E_LIVE === '1'
const liveLlmE2E = process.env.LINGWEN_E2E_LIVE_LLM === '1'
const a11yE2E = process.env.LINGWEN_E2E_LIVE === '1'

const liveBackendSpecPattern =
  /(ripples-audit|decisions-resolve|creator-workspace|ask-flow|library-flow|more-hub|landing-nav|advance-produce|today-flow|insight-flow|studio-flow|settings-flow|workflows-flow|advance-batch-flow|cascade-runs-flow|entity-memory-flow|director-paths-flow|memory-gateway-flow|product-tools-flow|companion-full-path-flow|companion-selection-agent-flow|modal-interaction|url-deep-linking|error-states|form-validation|export-flow|cross-tab-persistence)\.spec\.js/

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
  env: {
    PYTHONPATH: NOVEL_FACTORY_ROOT,
  },
}

export default defineConfig({
  testDir: './tests/e2e-smoke',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'list',
  snapshotPathTemplate: '{testDir}/{testFileDir}/snapshots/{arg}{ext}',
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
      testMatch: QUARANTINE_ONLY
        ? liveBackendSpecPattern
        : liveBackendSpecPattern,
      grep: QUARANTINE_ONLY ? /@quarantine/ : undefined,
      grepInvert: QUARANTINE_ONLY ? undefined : /@quarantine/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'live-llm',
      testMatch: /agent-plan-llm-flow\.spec\.js/,
      grep: /@live-llm/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'a11y-l1',
      testMatch: /a11y-l1\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      // Phase 115 Task 20 — Immersive Write Workspace v1 E2E.
      // Reads from /write/:chapterId; mocks /api/write/* via page.route so it
      // can run under the standard vite dev server without the live backend.
      // NOTE: Currently BLOCKED — the dev server throws "Cannot set properties
      // of undefined (setting 'exports')" (Phase 110/111B/114 cytoscape issue,
      // see CLAUDE.md v14.2). Vue app fails to mount, so `workbench-root`
      // is never rendered. Test is staged for a future fix.
      name: 'write-workspace',
      testDir: './tests/e2e',
      testMatch: /write-workspace\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'visual-capture',
      testDir: './tests/visual-audit',
      testMatch: /capture\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'visual-regression',
      testDir: './tests/visual-audit',
      testMatch: /regression\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'ui-metrics',
      testDir: './tests/visual-audit',
      testMatch: /ui-metrics\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'web-vitals',
      testDir: './tests/e2e-smoke',
      testMatch: /web-vitals\.spec\.js/,
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.PW_BASE_URL || 'http://localhost:5173',
      },
    },
  ],
  webServer: (liveE2E || liveLlmE2E || a11yE2E) ? [dashboardServer, viteServer] : viteServer,
})
