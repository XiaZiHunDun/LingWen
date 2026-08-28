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
import noShallowRefMutation from './eslint-rules/no-shallowref-mutation.js'

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
        'no-shallowref-mutation': noShallowRefMutation,
      } },
    },
    rules: {
      'custom/testid-class-sync': 'warn',
      'custom/no-duplicate-hooks': 'error',
      'custom/require-optional-chain': 'warn',
      'custom/no-store-value-access': 'error',
      'custom/no-shallowref-mutation': 'error',
    },
  },

  // 33 shallowRef sites live in .ts/.js (Phase 77+78 wholesale conversions in
  // composables/stores). Vue parser not needed — use tsParser directly.
  {
    files: ['src/**/*.{ts,js}'],
    languageOptions: {
      parser: tsParser,
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    plugins: {
      'custom': { rules: {
        'no-shallowref-mutation': noShallowRefMutation,
      } },
    },
    rules: {
      'custom/no-shallowref-mutation': 'error',
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

  // Phase 126 v16.3 — DP-01..06 ESLint enforcement.
  // Block frontend from importing backend Python packages directly.
  // Frontend talks to backend ONLY via FastAPI (typed wrappers in src/api/*.ts).
  {
    files: ['src/**/*.{js,ts,vue}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: [
                'infra',
                'infra/*',
                'infra/**',
                '**/infra',
                '**/infra/*',
                '**/infra/**',
              ],
              message:
                'frontend MUST NOT import backend infra modules directly. ' +
                'Use typed wrappers in src/api/*.ts (which call FastAPI).',
            },
            {
              group: [
                'lingwen_creator',
                'lingwen_creator/*',
                'lingwen_creator/**',
                '**/lingwen_creator',
                '**/lingwen_creator/*',
                '**/lingwen_creator/**',
              ],
              message:
                'frontend MUST NOT import lingwen_creator directly. ' +
                'Use typed wrappers in src/api/*.ts (which call FastAPI).',
            },
          ],
        },
      ],
    },
  },

  // Phase 126 v16.3 — no_barrel_bypass.
  // Composables/stores/pages/components MUST import typed wrappers directly
  // (e.g. '@/api/cvg', '@/api/health'), NOT the api/index.js barrel.
  // The barrel is kept for test mocks + non-creator funcs (budgets/connectivity).
  // Excludes src/api/** (barrel itself + non-creator .js modules).
  {
    files: [
      'src/composables/**/*.{js,ts,vue}',
      'src/stores/**/*.{js,ts,vue}',
      'src/pages/**/*.{js,ts,vue}',
      'src/components/**/*.{js,ts,vue}',
    ],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: [
                '@/api/index',
                '@/api/index.js',
                '@/api/index.ts',
                '../api/index',
                '../api/index.js',
                '../../api/index',
                '../../api/index.js',
                '../../../api/index',
                '../../../api/index.js',
              ],
              message:
                'do not bypass typed wrappers via the api/index.js barrel. ' +
                'Import directly from the typed wrapper (e.g. @/api/cvg).',
            },
          ],
        },
      ],
    },
  },
]
