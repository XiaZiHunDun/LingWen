// tests/eslint-rules/no-restricted-imports.test.cjs — Phase 126 v16.3
// 验证 ESLint no-restricted-imports 配置 (frontend_isolation + no_barrel_bypass):
//  - frontend_isolation: 禁止 infra/* + lingwen_creator/* import in src/
//  - no_barrel_bypass: 禁止 @/api/index.js barrel in composables/stores/pages/components
//
// Strategy: ESLint Linter.verify() with inline flat-config blocks (mirrors
// eslint.config.js). Uses filename to trigger files glob in the relevant block.
// No need for minimatch — we explicitly pass the right block per test.

const { Linter } = require('eslint')
const path = require('path')

const DASHBOARD_ROOT = path.resolve(__dirname, '../..')

// Mirror of the relevant blocks from eslint.config.js (Phase 126 v16.3).
// Kept in sync manually; if eslint.config.js changes, update here too.
const FRONTEND_ISOLATION_BLOCK = {
  files: ['src/**/*.{js,ts,vue}'],
  languageOptions: { ecmaVersion: 2022, sourceType: 'module' },
  rules: {
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: [
              'infra', 'infra/*', 'infra/**',
              '**/infra', '**/infra/*', '**/infra/**',
            ],
            message:
              'frontend MUST NOT import backend infra modules directly. ' +
              'Use typed wrappers in src/api/*.ts (which call FastAPI).',
          },
          {
            group: [
              'lingwen_creator', 'lingwen_creator/*', 'lingwen_creator/**',
              '**/lingwen_creator', '**/lingwen_creator/*', '**/lingwen_creator/**',
            ],
            message:
              'frontend MUST NOT import lingwen_creator directly. ' +
              'Use typed wrappers in src/api/*.ts (which call FastAPI).',
          },
        ],
      },
    ],
  },
}

const NO_BARREL_BYPASS_BLOCK = {
  files: [
    'src/composables/**/*.{js,ts,vue}',
    'src/stores/**/*.{js,ts,vue}',
    'src/pages/**/*.{js,ts,vue}',
    'src/components/**/*.{js,ts,vue}',
  ],
  languageOptions: { ecmaVersion: 2022, sourceType: 'module' },
  rules: {
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: [
              '@/api/index', '@/api/index.js', '@/api/index.ts',
              '../api/index', '../api/index.js',
              '../../api/index', '../../api/index.js',
              '../../../api/index', '../../../api/index.js',
            ],
            message:
              'do not bypass typed wrappers via the api/index.js barrel. ' +
              'Import directly from the typed wrapper (e.g. @/api/cvg).',
          },
        ],
      },
    ],
  },
}

// Helper: lint code with a specific flat-config block + filename.
// filename should be RELATIVE to DASHBOARD_ROOT (flat config `files` is
// resolved against config base path, which defaults to cwd = DASHBOARD_ROOT).
function lintWith(block, filename, code) {
  const linter = new Linter()
  return linter.verify(code, [block], { filename })
}

// Simple test runner (no vitest dep — cjs + node:test would also work but
// keeping consistent with testid-class-sync.test.cjs which uses console.log).
let _ok = 0
let _fail = 0

function expectHasError(label, messages) {
  const errors = messages.filter((m) => m.ruleId === 'no-restricted-imports')
  if (errors.length > 0) {
    console.log(`✓ ${label} (${errors.length} error${errors.length === 1 ? '' : 's'})`)
    _ok++
  } else {
    console.log(`✗ ${label}`)
    console.log(`  expected no-restricted-imports error, got: ${JSON.stringify(messages, null, 2)}`)
    _fail++
  }
}

function expectNoError(label, messages) {
  const errors = messages.filter((m) => m.ruleId === 'no-restricted-imports')
  if (errors.length === 0) {
    console.log(`✓ ${label}`)
    _ok++
  } else {
    console.log(`✗ ${label}`)
    console.log(`  unexpected error: ${JSON.stringify(errors, null, 2)}`)
    _fail++
  }
}

console.log('Phase 126 v16.3 — no-restricted-imports regression tests')
console.log('=====================================================')

// ===== frontend_isolation (applies to all src/**/*.{js,ts,vue}) =====
const isolationCases = [
  { code: `import { foo } from 'infra/foo'`, desc: 'infra/foo' },
  { code: `import { foo } from 'infra'`, desc: 'infra (bare)' },
  { code: `import { foo } from 'lingwen_creator/foo'`, desc: 'lingwen_creator/foo' },
  { code: `import { foo } from 'lingwen_creator'`, desc: 'lingwen_creator (bare)' },
  { code: `import { foo } from 'lingwen_creator/foo/bar'`, desc: 'lingwen_creator/foo/bar' },
]
for (const { code, desc } of isolationCases) {
  const messages = lintWith(FRONTEND_ISOLATION_BLOCK, 'src/pages/Test.vue', code)
  expectHasError(`frontend_isolation fires on \`${desc}\``, messages)
}

// ===== no_barrel_bypass (composable context) =====
const barrelCases = [
  `import { foo } from '@/api/index.js'`,
  `import { foo } from '@/api/index'`,
  `import { foo } from '../api/index.js'`,
  `import { foo } from '../../api/index.js'`,
  `import { foo } from '../../../api/index.js'`,
]
for (const code of barrelCases) {
  const messages = lintWith(NO_BARREL_BYPASS_BLOCK, 'src/composables/Test.js', code)
  expectHasError(`no_barrel_bypass fires on \`${code}\``, messages)
}

// ===== positive cases (no error expected) =====
const positiveCases = [
  {
    block: NO_BARREL_BYPASS_BLOCK,
    file: 'src/composables/useFoo.js',
    code: `import { fetchCascadeRuns } from '@/api/cvg'`,
    desc: 'composable imports typed wrapper directly',
  },
  {
    block: NO_BARREL_BYPASS_BLOCK,
    file: 'src/pages/Foo.vue',
    code: `import { fetchChapters } from '@/api/health'`,
    desc: 'page imports typed wrapper directly',
  },
  {
    block: FRONTEND_ISOLATION_BLOCK,
    file: 'src/api/index.js',
    code: `import { fetchCascadeRuns } from './cvg.js'`,
    desc: 'barrel internal re-export (relative path)',
  },
]
for (const { block, file, code, desc } of positiveCases) {
  const messages = lintWith(block, file, code)
  expectNoError(`positive: ${desc}`, messages)
}

console.log('=====================================================')
console.log(`${_ok} passed, ${_fail} failed`)
if (_fail > 0) process.exit(1)