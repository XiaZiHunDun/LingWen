# Phase 79 — INP Measurement Improvement 设计

> **日期**: 2026-08-21
> **范围**: 1 spec file edit + 12 JSON regenerated + 1 baseline doc updated. 1 atomic commit.
> **基础**: master = `a7546b3d` (Phase 78 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 76 baseline §5 Top Issues #3 指出 INP not measurable (synthetic click 不触发 PerformanceObserver `event` entries). Phase 79 修复.

---

## 1. 背景

Phase 76 baseline (`docs/perf/playwright-web-vitals-baseline.md`) 记录 INP 全 null:

> **INP**: Not measurable (synthetic click limitation)

原因: spec `web-vitals.spec.js` 用 `page.evaluate(() => target.click())` — DOM-level synthetic click. Vue 3 click 监听器触发, 但 PerformanceObserver `event` type 不 fire (无 proper user gesture).

Phase 79 用 Playwright `page.locator(...).click()` — 真实 mouse interaction (mouseover → mousedown → mouseup → click) with proper gesture. PerformanceObserver `event` 应 fire, INP 应 capture.

---

## 2. 目标 & 非目标

### 目标

1. **改 web-vitals.spec.js**: synthetic click → `page.locator('button:visible').first().click()`
2. **Re-run baseline**: 12 tests → 12 JSON artifacts regenerated
3. **Update baseline doc**: INP table populated with real data
4. **不破坏**: 1549 unit tests + 31 e2e specs (含 web-vitals)
5. **1 atomic commit**

### 非目标

- 不动其他 metrics (LCP/CLS/FCP/TBT 已 OK)
- 不加 multi-element interaction
- 不做真实 form-fill / multi-step interactions
- 不动 Playwright config
- 不改 vite config
- 不重跑 Phase 77/78 验证 (perf 优化与 INP 测量独立)

---

## 3. Spec Change

### 3.1 Current (Phase 76 baseline spec)

File: `apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`

```js
// Synthetic interaction for INP
await page.evaluate(() => {
  const target = document.querySelector('button, a, [role="button"]');
  if (target) target.click();
});
```

### 3.2 New (Phase 79)

```js
// Real Playwright interaction (triggers PerformanceObserver 'event' entries)
try {
  await page.locator('button:visible').first().click({ timeout: 5000 });
} catch (err) {
  // Some routes may have no visible button (fallback)
  console.log(`[${slug} run ${run}] no clickable button: ${err.message.split('\n')[0]}`);
}
```

### 3.3 Rationale

- `page.locator('button:visible').first()` — first VISIBLE button (not hidden by CSS)
- `.click()` — Playwright performs real mouse interaction:
  - `mouseover`, `mouseenter`, `mousemove`
  - `mousedown`, `mouseup`
  - `click` event
  - Proper user gesture context (enables PerformanceObserver `event` entries)
- `timeout: 5000` — fail fast per route (5s is generous for click action)
- `.catch` fallback — routes without visible button (e.g., loading state) still complete test

---

## 4. Re-baseline Plan

After spec edit:
1. Start dev server (`pnpm dev --port 5173`)
2. Run `pnpm exec playwright test --project=web-vitals --reporter=line --workers=1`
3. Capture 12 JSON artifacts (overwrite Phase 76's)
4. Compute new medians
5. Update baseline doc INP section

Expected:
- LCP/CLS/FCP/TBT unchanged (same loading pattern)
- INP now non-null for routes with clickable buttons
- INP may be null for routes without visible button at click time

---

## 5. Doc Update

File: `docs/perf/playwright-web-vitals-baseline.md`

Changes:
- §2 Per-route metrics table — add INP column data
- §3 Compliance — update INP row with real measurements
- §1 Summary — note INP now measurable
- §5 Top Issues — remove #3 (INP not measurable)
- §6 Phase 79+ Action Items — mark INP improvement as done

---

## 6. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1549 PASS | ✓ (unchanged — spec is test infra) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| 12 JSON artifacts updated | ✓ (Phase 76 overwrites) |
| Baseline doc INP section populated | ✓ |
| Re-run Playwright spec passes 12 tests | ✓ |
| `git diff --stat` 3 entries (1 spec + 12 JSON + 1 doc = 14 files, 0 modified app code) | ✓ |

---

## 7. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Click 触发 navigation 离开目标 route | Medium | INP 不准确 (测量 next page 加载) | 选 first visible button (likely UI control, not nav) |
| Some routes 无 clickable button at click time | Medium | INP 仍 null | `.catch()` + console.log |
| INP 值偏高 (dev mode, HMR overhead) | Medium | baseline noise | doc 说明 dev mode 限制 |
| Click triggers SPA route change before metrics collected | Low | metrics invalid | Wait 3s after click (already in spec) |

---

## 8. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Edit spec
# Edit apps/dashboard/tests/e2e-smoke/web-vitals.spec.js (line ~78)

# Re-run baseline (writes 12 JSON files)
cd apps/dashboard
pnpm dev --port 5173 --strictPort &
sleep 5
PW_BASE_URL=http://localhost:5173 pnpm exec playwright test --project=web-vitals \
  --reporter=line --workers=1 2>&1 | tail -20
kill $PREVIEW_PID 2>/dev/null

# Update baseline doc with new INP data
# Edit docs/perf/playwright-web-vitals-baseline.md (multiple sections)

git add apps/dashboard/tests/e2e-smoke/web-vitals.spec.js \
        docs/perf/playwright-web-vitals-baseline.md \
        docs/perf/playwright/

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "test(perf): real Playwright click for INP measurement (Phase 79)" \
    -m "Phase 79 INP measurement improvement (per Phase 76 baseline §5):

Spec change (web-vitals.spec.js):
- page.evaluate(() => target.click()) → page.locator('button:visible').first().click()
- Real mouse interaction triggers PerformanceObserver 'event' entries
- INP now measurable (was null due to synthetic click)

Baseline update:
- 12 JSON artifacts regenerated with INP data
- docs/perf/playwright-web-vitals-baseline.md INP section populated
- Top Issues #3 (INP not measurable) resolved

Phase 76 baseline (commit c9884e87) showed INP=null across all routes.
Phase 79 closes that gap.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

---

## 9. 测试策略

无新增 tests. Web-vitals spec 本身就是 e2e test. 1549 unit tests unchanged.

---

## 10. 后续

Phase 80+ 候选 (per Phase 79 + Handoff §6):

1. **Phase 80**: Bundle split (vendor 407kB / mermaid 390kB → lazy load)
2. **Phase 81**: Live e2e verification (Phase 66 6 specs)
3. **Phase 82**: CLAUDE.md v13.1 housekeeping
4. **Phase 83**: `no-shallowref-mutation` ESLint rule
5. **Phase 84**: 7 dead `mergePreset*` refs cleanup
6. **Phase 85**: Phase 78 spec housekeeping
