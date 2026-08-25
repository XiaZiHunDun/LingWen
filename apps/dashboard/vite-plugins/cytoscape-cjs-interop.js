// apps/dashboard/vite-plugins/cytoscape-cjs-interop.js
// Phase 111C — Vite plugin that wraps cytoscape-fcose / cose-base (and their
// UMD-wrapped deps) so they execute as CJS in the browser, then exports the
// resulting `module.exports` as ESM default.
//
// Background (see docs/superpowers/audit/2026-08-25-phase110-vite-preview-js-error-audit.md):
// cytoscape-fcose, cytoscape-cose-bilkent, cose-base, and layout-base are
// webpack-bundled UMD packages. rollup's @rollup/plugin-commonjs fails on
// their nested `module.exports = ...` patterns inside webpackBootstrap,
// producing the runtime error "Cannot set properties of undefined (setting
// 'exports')" in vite preview (prod build).
//
// Strategy: run the UMD in a context where `module`, `exports`, and `require`
// are defined globals. This forces the UMD to take its CJS branch, which
// assigns `module.exports = factory(require(dep))`. The factory body uses its
// own internal webpack runtime (with its own `module` references via closure),
// so our outer `module` only gets the final `module.exports` value — which we
// then re-export as ESM default.
//
// Run at the `load` hook with `enforce: 'pre'` to intercept the file before
// vite/rollup's built-in CJS processing.

import fs from 'node:fs'

// Packages whose UMD wrapper fails under rollup's CJS plugin.
// Their bare-specifier require() deps are listed below.
const INTERCEPT_PACKAGES = [
  'cytoscape-fcose',
  'cytoscape-cose-bilkent',
  'cose-base',
  'layout-base',
]

// Map of bare specifiers used by these UMDs to the ESM modules they resolve to.
// These imports will be inlined into each intercepted file's wrapped output.
const REQUIRE_RESOLVERS = `
const __coseInteropDeps__ = {
  'cose-base': () => __coseInteropDeps__.coseBase,
  'layout-base': () => __coseInteropDeps__.layoutBase,
};
const require = (n) => {
  const r = __coseInteropDeps__[n];
  if (!r) throw new Error('cytoscape-cjs-interop: unknown require "' + n + '"');
  return r();
};
`

const INTERCEPT_PATTERN = new RegExp(
  `[\\\\/]node_modules[\\\\/](?:${INTERCEPT_PACKAGES.join('|')})[\\\\/]`
)

// Map each intercepted package to the set of imports it needs.
const IMPORTS_BY_PACKAGE = {
  'cytoscape-fcose': `import __coseInteropDeps__coseBase from 'cose-base';\nimport __coseInteropDeps__layoutBase from 'layout-base';`,
  'cytoscape-cose-bilkent': `import __coseInteropDeps__coseBase from 'cose-base';\nimport __coseInteropDeps__layoutBase from 'layout-base';`,
  'cose-base': `import __coseInteropDeps__layoutBase from 'layout-base';`,
  'layout-base': '',
}

function matchPackage(id) {
  for (const pkg of INTERCEPT_PACKAGES) {
    if (id.includes(`/node_modules/${pkg}/`)) return pkg
  }
  return null
}

export function cytoscapeCjsInterop() {
  return {
    name: 'cytoscape-cjs-interop',
    enforce: 'pre',

    async load(id) {
      const pkg = matchPackage(id)
      if (!pkg) return null

      const source = fs.readFileSync(id, 'utf8')
      const imports = IMPORTS_BY_PACKAGE[pkg] || ''

      // Wrap in IIFE to scope webpack runtime variables (`a`, `i`, `n`, etc.)
      // which would otherwise collide between cose-base / cytoscape-fcose /
      // cytoscape-cose-bilkent bundles inlined into the same chunk.
      //
      // Returns the captured module.exports from inside the IIFE.
      const wrapped = `
// === Phase 111C: cytoscape-cjs-interop wrapper for ${pkg} ===
${imports}
const __coseInteropModule__ = (function() {
  const module = { exports: {} };
  const exports = module.exports;
${REQUIRE_RESOLVERS}
${source}
  return module.exports;
})();
export default __coseInteropModule__;
`

      return wrapped
    },
  }
}