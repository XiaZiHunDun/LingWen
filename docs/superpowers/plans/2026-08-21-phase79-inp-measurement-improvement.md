# Phase 79 Implementation Plan — INP Measurement Improvement

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace synthetic click with real Playwright `page.locator(...).click()` to capture real INP measurements. Re-run baseline. Update doc.

**Architecture:** Spec change is 1 file edit. Then dev server + Playwright re-run + JSON regeneration + doc update. 1 atomic commit.

**Tech Stack:** Playwright 1.61.1, Chromium 1228, vite dev (port 5173), PerformanceObserver `event` API.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase79-inp-measurement-improvement-design.md` (commit `96802007`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/tests/e2e-smoke/web-vitals.spec.js` | **Modify** (line ~78: synthetic click → page.click) |
| `docs/perf/playwright/*.json` | **Overwrite** (12 files regenerated) |
| `docs/perf/playwright-web-vitals-baseline.md` | **Modify** (INP section populated, Top Issues updated) |

**Total**: 14 files modified, 1 atomic commit.

---

## Task 1: Edit web-vitals.spec.js

**Files:**
- Modify: `apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`

- [ ] **Step 1.1: Locate current synthetic click code**

Run: `grep -n "Synthetic interaction" apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`
Expected: 1 hit around line 78.

- [ ] **Step 1.2: Read current block for exact text**

Run: `sed -n '74,85p' apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`

- [ ] **Step 1.3: Edit synthetic click block**

Use Edit tool. Replace the synthetic click block (lines 74-80 approximately) with:

```js
        // Real Playwright interaction (triggers PerformanceObserver 'event' entries)
        try {
          await page.locator('button:visible').first().click({ timeout: 5000 });
        } catch (err) {
          // Some routes may have no visible button (fallback)
          console.log(`[${slug} run ${run}] no clickable button: ${err.message.split('\n')[0]}`);
        }
```

- [ ] **Step 1.4: Verify file syntax**

Run: `node -c apps/dashboard/tests/e2e-smoke/web-vitals.spec.js && echo "syntax OK"`

---

## Task 2: Start dev server

**Files:** None

- [ ] **Step 2.1: Start dev server in background**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm dev --port 5173 --strictPort`
Use `run_in_background: true`.

- [ ] **Step 2.2: Wait + verify**

Run: `sleep 5 && curl -sf http://localhost:5173/ -o /dev/null && echo "dev OK"`

---

## Task 3: Run Playwright spec (regenerate 12 JSON artifacts)

**Files:**
- Overwrite: `docs/perf/playwright/*.json` (12 files)

- [ ] **Step 3.1: Run spec**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
PW_BASE_URL=http://localhost:5173 pnpm exec playwright test \
  --project=web-vitals \
  --reporter=line \
  --workers=1 \
  2>&1 | tail -30
```

Expected: 12 tests PASS, each with INP data populated.

- [ ] **Step 3.2: Verify 12 JSON artifacts updated**

Run: `ls -la docs/perf/playwright/*.json | wc -l`
Expected: 12

- [ ] **Step 3.3: Spot check INP data is non-null**

Run:
```bash
for f in /home/ailearn/projects/LingWen/docs/perf/playwright/*.json; do
  cat "$f" | grep -A1 inp
done
```

Expected: At least some `inp` values should be non-null (was null in Phase 76).

---

## Task 4: Stop dev server

**Files:** None

- [ ] **Step 4.1: Kill dev server**

If you used TaskOutput background, call TaskStop on the task ID. Or:
```bash
kill $(lsof -t -i:5173) 2>/dev/null
```

- [ ] **Step 4.2: Verify port freed**

Run: `lsof -i:5173 2>&1 | head -3 || echo "port 5173 free"`

---

## Task 5: Compute new medians + update baseline doc

**Files:**
- Modify: `docs/perf/playwright-web-vitals-baseline.md`

- [ ] **Step 5.1: Read all 12 JSON files + extract INP data**

Run:
```bash
cd /home/ailearn/projects/LingWen/docs/perf/playwright
for f in *.json; do echo "=== $f ==="; cat "$f"; echo; done
```

Compute medians per route (4 routes × 5 metrics = 20 cells, including new INP data).

- [ ] **Step 5.2: Update §2 Per-route metrics table**

Edit `docs/perf/playwright-web-vitals-baseline.md`:
- Add INP column data (real measurements, not "null")
- Update rows with actual median values

- [ ] **Step 5.3: Update §1 Summary**

Replace text about "INP 无法测量" with "INP now measurable: <median values>"

- [ ] **Step 5.4: Update §3 Compliance table**

Update INP row with real ✓/✗ status per route.

- [ ] **Step 5.5: Update §5 Top Issues**

Remove #3 (INP not measurable). Note "Phase 79 resolved this — INP now measurable via page.click()".

- [ ] **Step 5.6: Update §6 Phase 77+ Action Items**

Mark INP improvement as done. Add note: "Phase 79 closed this gap".

- [ ] **Step 5.7: Update § Methodology details**

Add note: "Phase 79: page.click() (real Playwright mouse interaction) replaces page.evaluate(target.click()) (synthetic DOM click)".

---

## Task 6: Final verifications

**Files:** None

- [ ] **Step 6.1: pnpm test**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1549 passed (1549)`

- [ ] **Step 6.2: vue-tsc**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors

- [ ] **Step 6.3: Build**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -5`
Expected: `✓ built in <time>`

- [ ] **Step 6.4: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git status -s`
Expected: 14 files modified (1 spec + 12 JSON + 1 doc).

---

## Task 7: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 7.1: Stage 14 files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/tests/e2e-smoke/web-vitals.spec.js \
        docs/perf/playwright-web-vitals-baseline.md \
        docs/perf/playwright/
```

- [ ] **Step 7.2: Verify staged**

Run: `git status -s`
Expected: 1 modified spec + 1 modified doc + 12 modified JSON files (some may show as M, some as rewrite).

- [ ] **Step 7.3: Commit**

Run:
```bash
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

- [ ] **Step 7.4: Verify commit**

Run: `git show --stat HEAD | head -20`
Expected: 14 files changed (1 .js + 12 .json + 1 .md).

- [ ] **Step 7.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §3.1 (current code) → Task 1.1-1.2
- Spec §3.2 (new code) → Task 1.3
- Spec §4 (re-baseline plan) → Tasks 2-4
- Spec §5 (doc update) → Task 5
- Spec §6 (verification) → Task 6
- Spec §8 (1 atomic commit) → Task 7

**Placeholder scan**:
- All Edit patterns have actual code
- All commands have expected output

**Risks covered**:
- Click navigation risk noted; fallback `.catch()` handles missing buttons
- Doc update explicitly notes dev mode limitation
- Final verifications catch any regression
