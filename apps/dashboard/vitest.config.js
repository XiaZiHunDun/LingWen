// vitest.config.js — Phase 8.30
// vitest 真 e2e 配置 (jsdom + @vue/test-utils)
// 跟 vite.config.js 共享 alias '@' → './src' (vitest 测试 import Vue component)
// 环境 jsdom (不需 browser), 跑 component-level unit test, 替代 ceremonial Playwright
// specs. 11 ceremonial specs 中 1 (pilot: cost-bar-chart-tier-mode.spec.ts) 先
// 验证 vitest 跑通, 后续 10 specs 批量改写.
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config.js'

export default mergeConfig(viteConfig, defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    // Phase 8.30: tests/unit/setup.ts 集中 stub echarts 等 jsdom-incompatible 模块
    setupFiles: ['./tests/unit/setup.ts'],
    include: ['src/**/*.spec.{js,ts}', 'tests/unit/**/*.spec.{js,ts}'],
    // Phase 9.31 F15: ceremonial Playwright specs 已删, 契约全走 tests/unit/
    exclude: ['node_modules', 'dist', 'tests/e2e/**', 'tests/e2e-smoke/**', 'coverage/**'],
    // Phase 8.43.2: pool: 'forks' jsdom fork-isolate 防 OOM (跟 Phase 6.4 pytest
    // forks 镜像, 多 spec 跑不串). coverage/** exclude 给 Phase 8.44+ 留占位.
    pool: 'forks',
    // Phase 8.44.1: v8 coverage provider, threshold 70/60, 跟 backend --cov-fail-under=30
    // 不对齐 (backend 历史债大, 后期慢慢提), 0 改 16 spec (coverage 是观察者).
    // reporter text/lcov/html 三档, lcov 给 Codecov (Phase 8.44.4), html 给本地 debug.
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      include: ['src/**/*.{js,ts,vue}'],
      exclude: ['src/**/*.spec.{js,ts}', 'src/main.ts', 'src/**/index.ts'],
      // Phase 9.57 F48: lines/functions stepped toward 80%; branches/statements follow measured baseline
      thresholds: { lines: 80, branches: 70, functions: 70, statements: 80 },
    },
  },
}))
