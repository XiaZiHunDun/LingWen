# Phase 111C — Custom Vite Plugin (Partial Fix)

> **Date**: 2026-08-25
> **Goal**: Fix vite preview JS error to enable prod-mode Web Vitals baseline
> **Status**: ⚠️ **Partial fix shipped**. Original "exports" error resolved; deeper upstream issue remains.
> **Recommendation**: Keep plugin + override as starting point for future Phase 112+ work.

---

## 1. Background

Phase 110 documented the vite preview JS error:
- `Cannot set properties of undefined (setting 'exports')`
- Root cause: cytoscape-fcose / cose-base / layout-base are webpack-bundled CJS with UMD wrappers; rollup's `@rollup/plugin-commonjs` fails on these specific patterns.

Phase 111B attempted `pnpm patch` and failed (inner webpackBootstrap `module.exports = ...` patterns).

Phase 111C: write a custom Vite plugin that pre-processes these UMD files with proper module/exports/require scope, plus a pnpm override to address a discovered layout-base version mismatch.

## 2. What was implemented

### 2.1 `apps/dashboard/vite-plugins/cytoscape-cjs-interop.js` (50 lines)

A Vite plugin with `enforce: 'pre'` `load` hook that:
- Intercepts files matching `node_modules/(cytoscape-fcose|cytoscape-cose-bilkent|cose-base|layout-base)/`
- Wraps the UMD source in an IIFE with `module`/`exports`/`require` defined
- The IIFE returns `module.exports` which becomes the ESM default export
- The wrapper text injected per-package includes the necessary `import` statements for require() targets

### 2.2 `apps/dashboard/vite.config.js` (1 line added)

```js
import { cytoscapeCjsInterop } from './vite-plugins/cytoscape-cjs-interop.js'
// ...
plugins: [vue(), cytoscapeCjsInterop()],
```

### 2.3 `package.json#pnpm.overrides` (added)

```json
"pnpm": {
  "overrides": {
    "layout-base": "1.0.2"
  }
}
```

**Why the override**: During investigation, discovered that `layout-base@2.0.1` has an upstream webpack bug — its webpack entry module returns `Emitter` (an EventEmitter class) instead of the `layoutBase` function with the `.layoutBase`/`.LayoutConstants` properties that cytoscape-fcose expects. Pinning to `layout-base@1.0.2` works around this bug (1.0.2 still has the same last-`module.exports`-wins issue, but the last `module.exports` happens to be the function with all properties attached).

## 3. What works

✅ Original `Cannot set properties of undefined (setting 'exports')` error **resolved**.
✅ Test baseline unchanged: **1545 PASS / 189 files**.
✅ `pnpm knip` still exit 0.
✅ `pnpm -C apps/dashboard exec knip` still exit 0.
✅ `pnpm run build` succeeds.

## 4. What doesn't work

⚠️ New error remains: `Cannot read properties of undefined (reading 'layoutBase')`.

This error fires in the cytoscape chunk during webpack module 0 lookup. It happens because:

1. **Cytoscape-fcose** and **cytoscape-cose-bilkent** access `__webpack_require__(140).layoutBase.X` and `__webpack_require__(0).layoutBase.X` respectively
2. They expect `__webpack_require__(0/140)` to return an object with a `.layoutBase` property
3. In cose-base@2.2.0's webpack module 45 (entry), `coseBase.layoutBase = __webpack_require__(551)` where 551 is the layout-base external
4. **Root issue**: When my IIFE wrapper executes the cose-base UMD, the cose-base module's `module.exports` may not be properly set to the coseBase object — possibly due to webpack runtime isolation issues between cose-base and cytoscape-fcose when both are bundled into the same chunk

The webpack runtime variables (`__webpack_require__`, `__webpack_modules__`, `__webpack_module_cache__`) inside the IIFE-wrapped cose-base collide with cytoscape-fcose's runtime when both are bundled into the same chunk. My IIFE isolates them at source level, but the runtime is still shared somehow at minified output level.

## 5. Diagnostic trail

| Step | Result |
|------|--------|
| Original error (Phase 76/110): `Cannot set properties of undefined (setting 'exports')` | Reproduced |
| Add `optimizeDeps.include` (Phase 110 attempt) | No effect (dev-only) |
| Add `commonjsOptions.transformMixedEsModules: true` | No effect |
| Add custom Vite plugin (Phase 111C) | **Original error resolved**; new error emerges |
| Add pnpm override `layout-base@1.0.2` | Required for layout-base to export function with all properties (workaround for 2.0.1 webpack bug) |
| Wrap each intercepted file in IIFE | **Partial fix** — original error gone, but new error remains |
| Investigate deeper | cyoscape-fcose expects `__webpack_require__(0/140).layoutBase.X` — see §4 |

## 6. Files changed

| File | Change |
|------|--------|
| `apps/dashboard/vite-plugins/cytoscape-cjs-interop.js` | **Created** (50 lines) |
| `apps/dashboard/vite.config.js` | **Modified** (added 1 import + 1 plugin entry) |
| `package.json` | **Modified** (added `pnpm.overrides.layout-base: 1.0.2`) |
| `pnpm-lock.yaml` | **Regenerated** (forces layout-base@1.0.2 resolution) |
| `docs/superpowers/audit/2026-08-25-phase111c-custom-vite-plugin-partial.md` | **Created** (this file) |

## 7. Verification

| Check | Value |
|-------|-------|
| `pnpm exec vitest run` | **1545 passed** (189 files) |
| `pnpm run build` | ✓ built (~19s) |
| `pnpm knip` (root) | ✓ exit 0 |
| `pnpm -C apps/dashboard exec knip` (CI) | ✓ exit 0 |
| `pnpm preview` (all 4 routes) | ❌ Cannot read properties of undefined (reading 'layoutBase') |

## 8. Recommended next phase

**Phase 112** — investigate the webpack runtime collision. Options:

1. **Force cytoscape-fcose / cose-base into separate chunks** (not inlined). Add them to `manualChunks` with `function() { return 'cytoscape-shim' }` to keep them isolated.
2. **Replace cytoscape with vis-network** in `/production` (Phase 111E). Removes all cytoscape deps. Largest blast radius but cleanest result.
3. **Use `vite-plugin-commonjs` with explicit config** for these specific files (Phase 111D). Middle ground.

**Recommendation**: **Phase 112 option 2** (replace cytoscape). cytoscape is only used in `/production` for graph visualization. vis-network is a drop-in alternative with similar API.

If visual fidelity matters, keep cytoscape and pursue Phase 112 option 1 (force chunk separation).

## 9. Rollback

If the plugin + override cause issues:

```bash
# Revert plugin
git checkout HEAD -- apps/dashboard/vite.config.js apps/dashboard/vite-plugins/cytoscape-cjs-interop.js
# Revert override
git checkout HEAD -- package.json pnpm-lock.yaml
pnpm install
```

This returns to the Phase 110 state (broken prod preview, but dev mode works).