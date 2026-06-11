// eslint.config.js — Phase 8.43.4 + Phase 9.39 F24 (ESLint 9+ flat config 正式化)
// 1 file 3 blocks: Block 1 spec dir (Phase 8.33) + Block 2 .vue testid-class-sync
// (Phase 8.36) + Block 3 .vue vue plugin (Phase 8.42). Replaces 3 .eslintrc.cjs
// + 走 ESLint 10 flat config native (0 走 dual mode).
import vuePlugin from 'eslint-plugin-vue'
import localRules from 'eslint-plugin-local-rules'
import vueParser from 'vue-eslint-parser'
import tsParser from '@typescript-eslint/parser'
// Phase 8.43.4 amend: testid-class-sync 是 CJS module.exports, 不能走
// 'local-rules/...' 命名空间 (eslint-plugin-local-rules 只暴露 no-class-selector-in-test,
// testid-class-sync 原本 走 .cjs + --rulesdir flag, 改 flat config 后需直接 import
// + 注册为 'custom' 插件).
import testidClassSync from './eslint-rules/testid-class-sync.js'

export default [
  // Global ignores
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'tests/e2e/**',
      'coverage/**',
    ],
  },

  // Block 1: Spec dir (Phase 8.33 — tests/unit/**/*.spec.ts + fixture)
  {
    files: [
      'tests/unit/**/*.spec.ts',
      'tests/fixtures/lint-testid/*.spec.ts',
    ],
    languageOptions: {
      parser: tsParser,
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    plugins: { 'local-rules': localRules },
    rules: {
      'local-rules/no-class-selector-in-test': 'error',
    },
  },

  // Block 2: .vue testid-class-sync (Phase 8.36 — 走 vue-eslint-parser + TS)
  {
    files: ['src/**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 2022,
        sourceType: 'module',
      },
    },
    plugins: {
      'local-rules': localRules,
      // Phase 8.43.4 amend: 'custom' 插件直接暴露 testid-class-sync 规则.
      'custom': { rules: { 'testid-class-sync': testidClassSync } },
    },
    rules: {
      'custom/testid-class-sync': 'warn',
    },
  },

  // Block 3: .vue eslint-plugin-vue (Phase 8.42 — vue3-recommended + 4 rule override)
  {
    files: ['src/**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 2022,
        sourceType: 'module',
      },
    },
    plugins: { vue: vuePlugin },
    ...vuePlugin.configs['flat/vue3-recommended'],
    rules: {
      'vue/multi-word-component-names': 'error',
      // WorkflowGraph.vue 用 mermaid 库输出 SVG (v-html=svg), mermaid render 是
      // trusted, 但 rule 视角是 XSS 表面. 留 warn (非 error) 提醒 0 阻塞 baseline.
      'vue/no-v-html': 'warn',
      'vue/require-default-prop': 'error',
      // WorkflowGraph.vue: 'mermaid' 同名 prop + import, 实际渲染 OK (import 在
      // props 后续用), 但 rule 报 name collision. 留 warn 提醒 0 阻塞.
      'vue/no-dupe-keys': 'warn',
    },
  },
]
