// .eslintrc.cjs — Phase 8.33
// ESLint config 限定 spec dir, 加载本地 rule plugin.
// 0 走 .vue, 0 改 setup.ts, 0 误伤 production code.
module.exports = {
  root: true,
  env: { node: true, es2022: true },
  overrides: [
    {
      // Phase 8.33: 限定 spec dir, 0 走 .vue / setup.ts / vitest.config.js
      files: ['tests/unit/**/*.spec.ts', 'tests/fixtures/lint-testid/*.spec.ts'],
      parser: '@typescript-eslint/parser',
      parserOptions: { ecmaVersion: 2022, sourceType: 'module' },
      plugins: ['eslint-plugin-local-rules'],
      rules: {
        'local/no-class-selector-in-test': 'error',
      },
    },
  ],
}
