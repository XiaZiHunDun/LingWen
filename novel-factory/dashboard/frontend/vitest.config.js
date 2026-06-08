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
    // Phase 8.30: ceremonial Playwright specs (.spec.js) 仍保留作契约文档,
    // 但走 vitest 跑的是 tests/unit/ + src/ 下的真 e2e tests
    exclude: ['node_modules', 'dist', 'tests/e2e/**'],
  },
}))
