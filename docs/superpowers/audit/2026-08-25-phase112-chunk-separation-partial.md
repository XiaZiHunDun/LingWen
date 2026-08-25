# Phase 112 — Force Cytoscape Deps into Separate Chunk (Partial Fix)

> **Date**: 2026-08-25
> **Goal**: Use Vite chunk separation to isolate cytoscape-fcose / cose-base / layout-base, preventing module ID remapping when inlined.
> **Status**: ⚠️ **Partial fix shipped**. Original "exports" error resolved (Phase 111C); "layoutBase" error resolved (Phase 112); deeper "FDLayoutConstants" error remains.

---

## 1. Background

Phase 111C discovered that cytoscape-fcose, cose-bilkent, cose-base, and layout-base were being **inlined into the cytoscape chunk**, causing webpack module ID remapping that broke `__webpack_require__(140).layoutBase.X` lookups at runtime.

Phase 112 attempts to fix this by forcing each cytoscape-related dep into its own dedicated chunk (`cytoscape-shim`), preventing inlining into other chunks.

## 2. What was implemented

### 2.1 `apps/dashboard/vite.config.js` — NAMED chunk additions

Added 4 entries to `NAMED`:
```js
'cytoscape-fcose': 'cytoscape-shim',
'cytoscape-cose-bilkent': 'cytoscape-shim',
'cose-base': 'cytoscape-shim',
'layout-base': 'cytoscape-shim',
```

Also changed match pattern from `node_modules/${pkg}` to `node_modules/${pkg}/` (trailing slash) so `cytoscape` substring doesn't match `cytoscape-fcose`/`cytoscape-cose-bilkent`.

### 2.2 Chunk output

- Before: `cytoscape-XXX.js` (470 kB) — contained cytoscape-fcose, cose-base, cose-bilkent, layout-base inlined
- After:
  - `cytoscape-XXX.js` (444 kB) — main cytoscape only
  - `cytoscape-shim-XXX.js` (145 kB) — fcose + cose-bilkent + cose-base + layout-base (still inlined into ONE shim chunk)

The shim chunk isolates these from cytoscape main + vendor chunks, avoiding the cross-chunk module ID remapping issue from Phase 111C.

## 3. Error progression

| Phase | Error | Cause |
|-------|-------|-------|
| Phase 76 / 110 | `Cannot set properties of undefined (setting 'exports')` | Rollup CJS plugin fails on UMD wrappers |
| Phase 111C | `Cannot read properties of undefined (reading 'layoutBase')` | Webpack runtime inlining collision between cytoscape-fcose and cose-base when both inlined into cytoscape chunk |
| **Phase 112 (current)** | `Cannot read properties of undefined (reading 'FDLayoutConstants')` | Module ID remapping WITHIN the shim chunk. After combining all 4 webpack bundles into shim chunk, vite/rollup renumbers module IDs. cose-base's external module 551 (layout-base) gets renumbered to 0; but cose-bilkent accesses `__webpack_require__(0).FDLayoutConstants` — which is now a DIFFERENT module |

## 4. Root cause analysis (Phase 112 leftover)

When cytoscape-fcose / cose-bilkent / cose-base / layout-base are bundled together (whether inline or in one shim chunk), vite/rollup's module ID renumbering creates a mismatch:

1. cose-bilkent's webpack was built assuming **module 0 = cose-base** (external)
2. cose-base's webpack was built assuming **module 551 = layout-base** (external)
3. After combining, the renumbered IDs don't match the original
4. Accesses like `__webpack_require__(0).layoutBase.FDLayoutConstants` resolve to wrong modules
5. Result: `FDLayoutConstants` is undefined (because `__webpack_require__(0)` now returns a different cose-bilkent module that doesn't have `.FDLayoutConstants`)

This is a fundamental incompatibility between the bundled module structure of these packages and how vite/rollup combines them.

## 5. What works

✅ Original `Cannot set properties of undefined (setting 'exports')` error — **resolved** (Phase 111C)
✅ Phase 112 `Cannot read properties of undefined (reading 'layoutBase')` — **resolved**
✅ Tests still pass: **1545 / 189 files**
✅ Build clean
✅ knip gate still exit 0

## 6. What doesn't work

⚠️ `Cannot read properties of undefined (reading 'FDLayoutConstants')` on all 4 routes in prod preview.

## 7. Recommended next step

The remaining issue is fundamental — module ID renumbering inside the shim chunk. Options:

1. **Phase 112A** — Force each dep into its OWN chunk (not combined into shim). May avoid intra-chunk ID collisions. But cross-chunk imports still need to resolve.

2. **Phase 112B** — Custom Rollup plugin that explicitly maps module IDs (e.g., force cose-base's module 551 to keep its original ID). Complex, fragile.

3. **Phase 112C** (recommended) — Replace cytoscape with vis-network in `/production`. Removes cytoscape dependency entirely. Larger feature change but cleanest result.

4. **Phase 112D** — Accept dev-mode Web Vitals baseline as authoritative; defer prod baseline to future sessions.

## 8. Files changed in Phase 112

| File | Change |
|------|--------|
| `apps/dashboard/vite.config.js` | **Modified** — added 4 NAMED entries + changed match pattern |
| `docs/superpowers/audit/2026-08-25-phase112-chunk-separation-partial.md` | **Created** (this file) |

## 9. Combined state (Phase 110 + 111C + 112)

After all 3 phases, the following partial-fix code is in master:
- `apps/dashboard/vite-plugins/cytoscape-cjs-interop.js` (Phase 111C) — wraps UMDs in IIFE
- `apps/dashboard/vite.config.js` (Phase 111C + 112) — plugin + NAMED entries
- `package.json#pnpm.overrides` (Phase 111C) — pin layout-base@1.0.2
- `pnpm-lock.yaml` (Phase 111C) — regenerated

If a future session wants to fully revert to the Phase 76/95-baseline state (dev-mode Web Vitals only, no prod-mode attempts):

```bash
git revert <phase-111c-commit> <phase-112-commit>
pnpm install
```

## 10. Verification

| Check | Value |
|-------|-------|
| `pnpm exec vitest run` | **1545 passed** (189 files) |
| `pnpm run build` | ✓ built (~19s) |
| `pnpm knip` (root) | ✓ exit 0 |
| `pnpm -C apps/dashboard exec knip` (CI) | ✓ exit 0 |
| `pnpm preview` route `/` | ❌ Cannot read properties of undefined (reading 'FDLayoutConstants') |
| `pnpm preview` route `/creator` | ❌ Same error |
| `pnpm preview` route `/studio` | ❌ Same error |
| `pnpm preview` route `/production` | ❌ Same error |
| `pnpm dev` (port 5173) | ✅ Works (esbuild pre-bundling handles CJS correctly) |