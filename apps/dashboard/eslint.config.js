import vuePlugin from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'
import tsParser from '@typescript-eslint/parser'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const localRules = require('./eslint-local-rules.cjs')
const noClassSelectorInTest = localRules['no-class-selector-in-test']

import testidClassSync from './eslint-rules/testid-class-sync.js'
import noDuplicateHooks from './eslint-rules/no-duplicate-hooks.js'
import requireOptionalChain from './eslint-rules/require-optional-chain.js'
import noStoreValueAccess from './eslint-rules/no-store-value-access.js'

export default [
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'tests/e2e/**',
      'coverage/**',
    ],
  },

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
    plugins: {
      'custom': { rules: { 'no-class-selector-in-test': noClassSelectorInTest } },
    },
    rules: {
      'custom/no-class-selector-in-test': 'error',
    },
  },

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
      'custom': { rules: { 
        'testid-class-sync': testidClassSync,
        'no-duplicate-hooks': noDuplicateHooks,
        'require-optional-chain': requireOptionalChain,
        'no-store-value-access': noStoreValueAccess,
      } },
    },
    rules: {
      'custom/testid-class-sync': 'warn',
      'custom/no-duplicate-hooks': 'error',
      'custom/require-optional-chain': 'warn',
      'custom/no-store-value-access': 'error',
    },
  },

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
      'vue/no-v-html': 'warn',
      'vue/require-default-prop': 'error',
      'vue/no-dupe-keys': 'warn',
    },
  },

  // v-html 已审计豁免：WorkflowGraph (mermaid 生成的受信任 SVG),
  // CreatorMemorySearch (highlightMemorySnippet 已 escapeHtml 转义)
  {
    files: [
      'src/components/WorkflowGraph.vue',
      'src/components/creator/CreatorMemorySearch.vue',
    ],
    rules: {
      'vue/no-v-html': 'off',
    },
  },
]
