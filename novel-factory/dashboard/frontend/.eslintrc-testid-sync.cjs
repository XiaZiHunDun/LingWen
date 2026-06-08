// .eslintrc-testid-sync.cjs — Phase 8.36
// 独立 ESLint config for `lint:testid-sync` 命令. 仅 走 .vue, 加 vue-eslint-parser
// + sourceType: module (解析 <script> 块 import/export). 0 走 tests/, 0 走 setup.ts,
// 0 跟 Phase 8.33 .eslintrc.cjs 冲突 (那个限定 spec dir 走 .ts + local-rules plugin).
module.exports = {
  root: true,
  env: { node: true, es2022: true, browser: true },
  parser: 'vue-eslint-parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    parser: '@typescript-eslint/parser',  // <script lang="ts"> 走 TS parser
  },
  rules: {},
}
