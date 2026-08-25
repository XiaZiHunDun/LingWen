# Phase 114 Cytoscape Vite Alias Stub — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `pnpm preview` JS error to enable prod-mode Web Vitals baseline by aliasing the cytoscape family to a no-op ESM stub via Vite `resolve.alias`.

**Architecture:** mermaid 11.16's `architectureDiagram` chunk statically imports cytoscape/cytoscape-fcose/cytoscape-cose-bilkent/cose-base/layout-base, which are webpack-bundled UMD modules that rollup's `@rollup/plugin-commonjs` cannot wrap (`Cannot set properties of undefined (setting 'exports')`). Replace all 5 with a single ESM Proxy stub via Vite alias. LingWen only renders `graph TD` flowcharts (flowDetector_v2 never matches architecture syntax), so the stub is never actually invoked at runtime — it just removes the broken modules from the prod bundle.

**Tech Stack:** Vite 5+ (resolve.alias), Node.js ESM Proxy, Playwright 1.61 (verification).

---

## File Structure

| File | Change | Responsibility |
|------|--------|----------------|
| `apps/dashboard/scripts/cytoscape-stub.mjs` | **Create** | ESM Proxy stub for cytoscape family |
| `apps/dashboard/vite.config.js` | **Modify** | Add `resolve.alias` block for 5 cytoscape packages |

No source code changes. No dep changes. No test changes.

---

## Task 1: Create ESM Stub File

**Files:**
- Create: `apps/dashboard/scripts/cytoscape-stub.mjs`

- [ ] **Step 1: Write the stub file**

Create `apps/dashboard/scripts/cytoscape-stub.mjs` with this exact content:

```js
// apps/dashboard/scripts/cytoscape-stub.mjs
//
// No-op ESM stub for cytoscape family (cytoscape, cytoscape-fcose,
// cytoscape-cose-bilkent, cose-base, layout-base).
//
// Background: LingWen renders only `graph TD` flowcharts (mermaid
// flowDiagram chunk). mermaid 11.16 ships architecture diagrams in a
// separate chunk that statically imports the cytoscape family — which
// are webpack-bundled UMD modules that rollup's commonjs plugin cannot
// wrap (`Cannot set properties of undefined (setting 'exports')`).
// Aliasing these to a Proxy stub keeps the prod bundle clean. The
// architecture chunk is unreachable from our render path because
// flowDetector_v2 never matches `architecture` syntax.
//
// Stub semantics: any property access / call / construct returns a
// new Proxy — never undefined. This avoids TDZ violations if mermaid
// internals access cytoscape eagerly during startup.

const handler = {
  get(_target, prop) {
    if (prop === 'default') return proxy;
    if (prop === Symbol.toPrimitive) return undefined;
    return new Proxy(function () {}, handler);
  },
  apply() {
    return new Proxy({}, handler);
  },
  construct() {
    return new Proxy({}, handler);
  },
};

function proxy() {}

Object.setPrototypeOf(proxy, new Proxy(function () {}, handler));
proxy.default = proxy;

export default proxy;
```

- [ ] **Step 2: Verify file syntax**

Run: `cd /home/ailearn/projects/LingWen && node --check apps/dashboard/scripts/cytoscape-stub.mjs`
Expected: no output (exit 0). If syntax error, fix and re-run.

- [ ] **Step 3: Smoke-test the Proxy semantics**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && node -e "import('./scripts/cytoscape-stub.mjs').then(m => { const x = m.default; console.log(typeof x, typeof x(), typeof x.foo, typeof x.foo(), typeof x.default); })"`

Expected output:
```
function object function function function
```

If any throws, the Proxy is misconfigured. Re-check the file.

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/scripts/cytoscape-stub.mjs
git commit -m "feat(build): add cytoscape ESM stub for Vite alias (Phase 114)"
```

---

## Task 2: Wire Vite Alias

**Files:**
- Modify: `apps/dashboard/vite.config.js:1-82` (entire file, ~10 line addition)

- [ ] **Step 1: Read current vite.config.js**

Run: `cat apps/dashboard/vite.config.js`

Confirm current structure has `import { defineConfig } from 'vite'` on line 1 and `import vue from '@vitejs/plugin-vue'` on line 2.

- [ ] **Step 2: Add `node:url` import**

Replace line 1-2 with:

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

// === Phase 114: cytoscape family stub ===
// mermaid 11.16 architectureDiagram chunk statically imports
// cytoscape/cytoscape-fcose/cytoscape-cose-bilkent/cose-base/layout-base.
// These are webpack-bundled UMD modules that rollup's commonjs plugin
// can't wrap. Alias to no-op ESM stub because LingWen never renders
// architecture diagrams (only `graph TD` flowcharts).
const cytoscapeStubPath = fileURLToPath(
  new URL('./scripts/cytoscape-stub.mjs', import.meta.url)
)
const CYTOSCAPE_STUB_ALIASES = [
  { find: /^cytoscape$/, replacement: cytoscapeStubPath },
  { find: /^cytoscape-fcose$/, replacement: cytoscapeStubPath },
  { find: /^cytoscape-cose-bilkent$/, replacement: cytoscapeStubPath },
  { find: /^cose-base$/, replacement: cytoscapeStubPath },
  { find: /^layout-base$/, replacement: cytoscapeStubPath },
]
```

- [ ] **Step 3: Add `resolve.alias` to `defineConfig`**

Inside the `defineConfig({...})` object, add `resolve: { alias: CYTOSCAPE_STUB_ALIASES }` as the FIRST property after `plugins`:

```js
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: CYTOSCAPE_STUB_ALIASES,
  },
  server: {
    // ... existing server config unchanged
```

(The rest of the file — `server`, `build`, `root` — stays unchanged.)

- [ ] **Step 4: Verify file structure**

Run: `cd /home/ailearn/projects/LingWen && node --check apps/dashboard/vite.config.js` (it uses ESM via `"type": "module"` in package.json)

Expected: no output (exit 0).

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/vite.config.js
git commit -m "feat(build): alias cytoscape family to no-op stub in Vite (Phase 114)"
```

---

## Task 3: Verify Build + Tests + knip

**Files:** none (verification only)

- [ ] **Step 1: Run unit tests**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -10`

Expected: `Tests  1545 passed (189 files)` or similar. If count changes, investigate which test broke.

- [ ] **Step 2: Run vue-tsc**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -5`

Expected: no errors. (Note: vite.config.js is .js not .ts, so vue-tsc shouldn't care.)

- [ ] **Step 3: Run production build**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -30`

Expected:
- `✓ built in ~Xs`
- No `Circular chunk` warning for cytoscape
- No `cytoscape-*.js` chunk in `dist/assets/` (use `ls dist/assets/ | grep -i cytoscape` to verify)
- Existing chunks (vendor, mermaid, naive-ui, etc.) still emitted

If build fails, check vite.config.js syntax.

- [ ] **Step 4: Run knip (CI path)**

Run: `cd /home/ailearn/projects/LingWen && pnpm -C apps/dashboard exec knip 2>&1 | tail -10`

Expected: exit 0, no output. (stub file outside knip's project globs — should be invisible.)

- [ ] **Step 5: Run knip (root path)**

Run: `cd /home/ailearn/projects/LingWen && pnpm knip 2>&1 | tail -10`

Expected: exit 0.

---

## Task 4: Verify Dev Mode

**Files:** none (verification only)

- [ ] **Step 1: Start dev server in background**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm dev --port 5174 --strictPort 2>&1 | tee /tmp/dev.log`

Run in background (using `run_in_background: true`). Wait 5 seconds.

- [ ] **Step 2: Curl root route**

Run: `curl -s http://localhost:5174/ | head -c 500`

Expected: HTML with `<div id="app"></div>` or similar Vue mount point. Status 200.

- [ ] **Step 3: Render WorkflowsPage (uses mermaid)**

Run: `curl -s http://localhost:5174/workflows 2>&1 | head -c 200`

Expected: 200 status, Vue mount HTML. (The actual rendering needs JS to mount, so curl will only see the SPA shell.)

- [ ] **Step 4: Check dev log for errors**

Run: `grep -iE "error|cytoscape" /tmp/dev.log | head -10`

Expected: no cytoscape-related errors. (vue-ts warnings about unknown component are OK.)

- [ ] **Step 5: Stop dev server**

Run: `pkill -f "vite.*5174" || true`

---

## Task 5: Verify Prod Preview with Playwright

**Files:** none (verification only)

- [ ] **Step 1: Start preview server in background**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm preview --port 4173 --strictPort 2>&1 | tee /tmp/preview.log`

Run in background. Wait 4 seconds.

- [ ] **Step 2: Run Playwright body-length check**

Write `/tmp/check-preview-phase114.mjs`:

```js
import { chromium } from '/home/ailearn/projects/LingWen/apps/dashboard/node_modules/playwright/index.mjs';

const ROUTES = ['/', '/workflows', '/creator', '/creator/write'];
const browser = await chromium.launch();
const ctx = await browser.newContext();
const results = [];
for (const route of ROUTES) {
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(`http://localhost:4173${route}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  const bodyText = await page.evaluate(() => document.body.innerText.length);
  results.push({ route, bodyLength: bodyText, errors });
  await page.close();
}
await browser.close();
console.log(JSON.stringify(results, null, 2));
const allRendered = results.every(r => r.bodyLength > 0 && r.errors.length === 0);
process.exit(allRendered ? 0 : 1);
```

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && node /tmp/check-preview-phase114.mjs`

Expected output: each route has `bodyLength > 0` and `errors: []`. Exit code 0.

If any route has `bodyLength === 0` or non-empty `errors`, investigate:
- Check `/tmp/preview.log` for build warnings
- Check `dist/assets/` for unexpected chunks
- Check browser devtools network for failed chunk loads

- [ ] **Step 3: Stop preview server**

Run: `pkill -f "vite.*4173" || true`

- [ ] **Step 4: If fix worked, capture before/after comparison**

Note the bodyLength values for all 4 routes. Save to scratch (we'll include in commit message).

---

## Task 6: Run Prod Web Vitals Baseline

**Files:**
- Create: `docs/perf/web-vitals-prod-baseline-phase114.md` (results doc)

- [ ] **Step 1: Verify Playwright Web Vitals spec exists**

Run: `ls /home/ailearn/projects/LingWen/apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`

Expected: file exists. If not, the Web Vitals harness needs different setup — skip this task and proceed to Task 7 with a note in commit message.

- [ ] **Step 2: Start preview server**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm preview --port 4173 --strictPort 2>&1 | tee /tmp/preview-wv.log`

Run in background. Wait 4 seconds.

- [ ] **Step 3: Run Web Vitals baseline**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec playwright test tests/e2e-smoke/web-vitals.spec.js 2>&1 | tail -40`

Expected: 4 routes × 3 runs × 5 metrics = 60 measurements recorded. Pass/fail status against targets.

- [ ] **Step 4: Stop preview server**

Run: `pkill -f "vite.*4173" || true`

- [ ] **Step 5: Write baseline report**

Create `docs/perf/web-vitals-prod-baseline-phase114.md`:

```markdown
# Phase 114 — Prod Web Vitals Baseline

> **Date**: 2026-08-26
> **Goal**: Establish prod-mode (pnpm preview) Web Vitals baseline after cytoscape family stub
> **Status**: [PASS / PARTIAL / FAIL]

## Build

- Vite alias: cytoscape family → scripts/cytoscape-stub.mjs
- pnpm preview: [works / partial / fails]
- dist/assets/cytoscape-*.js: [absent / present]

## Measurements

| Route | LCP | CLS | FCP | TBT | INP | Run 1/2/3 |
|-------|-----|-----|-----|-----|-----|-----------|
| / | | | | | | |
| /workflows | | | | | | |
| /creator | | | | | | |
| /creator/write | | | | | | |

(3-run averages; if measurements unavailable, note "not captured" and reason)

## Comparison with Phase 106 (dev baseline)

| Route | LCP dev | LCP prod | Δ |
|-------|---------|----------|---|

(If dev baseline data available from docs/perf/playwright-web-vitals-baseline.md)

## Conclusion

[1-2 sentence summary: prod faster than dev (expected), or regression, or no change.]
```

Fill in actual values. Commit this doc with the implementation commit (next task).

---

## Task 7: Final Commit + Push

**Files:**
- Commit any pending changes (baseline report)

- [ ] **Step 1: Check git status**

Run: `cd /home/ailearn/projects/LingWen && git status`

Expected: clean or only baseline report untracked.

- [ ] **Step 2: Commit baseline report if any**

```bash
cd /home/ailearn/projects/LingWen
git add docs/perf/web-vitals-prod-baseline-phase114.md
git commit -m "docs(perf): Phase 114 prod Web Vitals baseline (cytoscape stub fix)"
```

(If report file already committed with Task 6 step, skip.)

- [ ] **Step 3: Verify final state**

Run: `git log --oneline -5`

Expected: Phase 114 spec commit + 2 implementation commits (stub file + vite.config.js) + baseline report commit.

- [ ] **Step 4: Push to master**

```bash
cd /home/ailearn/projects/LingWen
git push origin master
```

Expected: `* [new branch] master -> master` or `Everything up-to-date`. No errors.

---

## Self-Review Notes

**Spec coverage**:
- Section 3.1 stub file → Task 1
- Section 3.2 vite.config.js → Task 2
- Section 4 verification gates → Tasks 3-6
- Section 5 rollback → not explicitly a task (revert is implicit if any verification fails)
- Section 7 acceptance criteria → Tasks 3-7 collectively

**Placeholder scan**: No TBD/TODO/implement-later markers. All code blocks are complete.

**Type consistency**: `CYTOSCAPE_STUB_ALIASES` defined once in Task 2, reused in `resolve.alias`. `cytoscapeStubPath` used in 5 alias entries. No naming drift.

**Edge cases covered**:
- Step 3 Task 1: Proxy semantics smoke test catches misconfigured Proxy
- Step 3 Task 5: bodyLength > 0 is the canonical Vue mount verification (per Phase 112C lesson: don't trust 0-errors reports when body is empty)
- Step 5 Task 1: explicit check that web-vitals.spec.js exists before running it (defensive)

**Frequent commits**: 2 implementation commits + 1 docs commit. Each task that changes code commits at the end.