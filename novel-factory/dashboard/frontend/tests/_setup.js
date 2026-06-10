// tests/_setup.js — Phase 9.13 (e2e-shim for ripples.spec.js verbatim import)
// Re-export Playwright test/expect (跟 Phase 8.45.3 smoke.spec.js 用 @playwright/test 1:1).
// 0 shared fixtures / 0 custom hooks (Phase 9.13 留 YAGNI, 0 testid-class sync).
import { test, expect } from '@playwright/test';
export { test, expect };
