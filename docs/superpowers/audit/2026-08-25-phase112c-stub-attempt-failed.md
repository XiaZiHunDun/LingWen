# Phase 112C — Stub Plugin Attempt (Failed)

> **Date**: 2026-08-25
> **Goal**: Stub cytoscape deps as no-op modules to fix prod Web Vitals
> **Status**: ❌ **Attempt failed**. Current master state (cytoscape-cjs-interop + NAMED shim chunks) does NOT actually fix the prod preview error.
> **Recommendation**: Revert all partial fixes (Phase 111C + 112) — accept dev-mode Web Vitals as authoritative. OR escalate to custom rollup plugin with module ID mapping.

---

## 1. Background

Phase 76 documented the vite preview "Cannot set properties of undefined (setting 'exports')" error. Phases 110, 111B, 111C, 112 attempted various fixes, none fully successful. Phase 112 (chunk separation) appeared to work but the success was a measurement error.

After thorough re-verification with `apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`:
- All 4 routes in prod preview still fail with "Cannot read properties of undefined (reading 'FDLayoutConstants')"
- Vue app does NOT mount in prod (body.innerText.length === 0 for all routes)
- Dev mode (`pnpm dev`) still works correctly

## 2. Phase 112C attempt

### 2.1 Approach

Write a custom Vite plugin that intercepts `cytoscape-fcose`, `cytoscape-cose-bilkent`, `cose-base`, `layout-base` imports and returns a no-op Proxy stub. This avoids loading the actual UMD code.

**Rationale**: LingWen backend only generates `graph TD` flowchart syntax (verified at `infra/got/visualizer.py:80`). Flowcharts don't need cytoscape. Stubbing these deps should be invisible to our code.

### 2.2 Implementation

`apps/dashboard/vite-plugins/cytoscape-stub.js` (50 lines):
- `resolveId` hook returns virtual `\0cytoscape-stub` ID for the 5 target packages
- `load` hook returns stub source (Proxy that returns undefined for any access)

Updated `vite.config.js`:
- Replaced `cytoscapeCjsInterop` import with `cytoscapeStub`
- Reverted Phase 112 NAMED additions (not needed if deps are stubbed)

### 2.3 Test result

❌ Failed. New error: `Cannot access 'H' before initialization` (TDZ error in vendor chunk).

The stub plugin caused a different TDZ error somewhere in vendor chunk (some library's class initialization). After git stash + dropping the stub plugin changes, the original FDLayoutConstants error returns.

The stub plugin approach failed because:
1. Stubbing cytoscape-related deps leaves a gap in mermaid's dependency graph
2. Mermaid (or one of its other deps) accesses something that was previously provided by cytoscape stubs
3. The stub returning `undefined` for property access triggers a different initialization-order bug

## 3. Current actual master state

After Phase 112 commit (`8b6bed18`):
- `apps/dashboard/vite-plugins/cytoscape-cjs-interop.js` (Phase 111C) — UMD IIFE wrapper
- `apps/dashboard/vite.config.js` — adds cytoscapeCjsInterop plugin + NAMED entries for cytoscape-shim chunk
- `package.json#pnpm.overrides` — pin `layout-base: 1.0.2`
- `pnpm-lock.yaml` — regenerated

**Test results**:
- ✅ Dev mode (`pnpm dev`) works — Vue mounts, all 4 routes render
- ❌ Prod mode (`pnpm preview`) — all 4 routes fail with `Cannot read properties of undefined (reading 'FDLayoutConstants')`. Vue does NOT mount.

## 4. Lessons learned

1. **Don't trust partial verification**: My earlier "0 errors" report from `/tmp/check-preview-2.mjs` was misleading. The body.length=0 should have been a red flag — Vue wasn't mounting, just no error was thrown before page.close(). The proper test is `body.length > 0` (which the spec enforces) and `expect(bodyText).toBeGreaterThan(0)`.

2. **Mermaid is tightly coupled to cytoscape**: Stubbing cytoscape deps out entirely breaks mermaid's initialization. The cytoscape code path is loaded eagerly regardless of whether it's actually used for rendering.

3. **The "exports" → "layoutBase" → "FDLayoutConstants" progression** in earlier phases was real progress on the same root cause, not three separate issues. The webpack module ID renumbering problem affects ALL access patterns.

## 5. Recommended next step

Three options:

### Option A (Recommended): Revert all partial fixes (Phase 111C + 112)
```bash
git revert 3a607819^..be7b1dde  # revert Phase 106 commit's children
# OR more surgically:
git revert be7b1dde 8b6bed18
pnpm install  # refresh pnpm-lock.yaml
```
- Returns master to Phase 105b state (only Phase 106 + 109 + housekeeping + audit commits remain)
- Dev Web Vitals baseline (Phase 106) remains authoritative
- Future attempts can start fresh

### Option B: Custom rollup plugin with module ID mapping
- Write a rollup plugin that intercepts module IDs of cytoscape/cose-base/layout-base
- Force them to keep their original webpack IDs (551, 0, etc.) when combined into shim chunk
- High complexity, low success probability

### Option C: Replace cytoscape entirely (vis-network or similar)
- Touches `/production` WorkflowGraph component
- Requires API rewrite
- 2-4 hours of feature work
- Best long-term solution

## 6. What was added in Phase 112C attempt

| File | Change | Status |
|------|--------|--------|
| `apps/dashboard/vite-plugins/cytoscape-stub.js` | Created (50 lines) | **Deleted** (reverted to clean state) |
| `apps/dashboard/vite.config.js` | Modified (stub plugin import) | **Reverted** to Phase 112 state |
| `docs/superpowers/audit/2026-08-25-phase112c-stub-attempt-failed.md` | Created (this file) | **Kept** for future reference |

## 7. Verification

| Check | Value |
|-------|-------|
| `pnpm exec vitest run` | **1545 passed** (189 files) |
| `pnpm run build` | ✓ built (~20s) |
| `pnpm knip` (root) | ✓ exit 0 |
| `pnpm -C apps/dashboard exec knip` (CI) | ✓ exit 0 |
| `pnpm dev` (port 5173) | ✅ Works (all 4 routes render) |
| `pnpm preview` (port 5173/4173) | ❌ Cannot read properties of undefined (reading 'FDLayoutConstants') |