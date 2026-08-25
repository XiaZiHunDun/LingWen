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
// Stub semantics: proxy IS a Proxy wrapping a no-op function. Every
// call / access / construct returns a new Proxy — never undefined.
// This avoids TDZ violations AND chained access (`.layout().run()`)
// in any mermaid internal that may eagerly touch cytoscape.

const handler = {
  get(_target, prop) {
    if (prop === 'default') return proxy;
    if (prop === Symbol.toPrimitive) return undefined;
    return new Proxy(function () {}, handler);
  },
  apply() {
    return new Proxy(function () {}, handler);
  },
  construct() {
    return new Proxy(function () {}, handler);
  },
};

const proxy = new Proxy(function () {}, handler);

export default proxy;