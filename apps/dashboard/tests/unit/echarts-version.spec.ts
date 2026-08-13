// tests/unit/echarts-version.spec.ts — Phase 9.54 F43
// Smoke: ECharts 6.x modular imports resolve after upgrade.

import { describe, test, expect } from 'vitest'

describe('ECharts 6.x modular imports (Phase 9.54 F43)', () => {
  test('echarts/core init export available', async () => {
    const echarts = await import('echarts/core')
    expect(typeof echarts.init).toBe('function')
  })

  test('GraphChart and CanvasRenderer register without error', async () => {
    const echarts = await import('echarts/core')
    const { GraphChart } = await import('echarts/charts')
    const { CanvasRenderer } = await import('echarts/renderers')
    const { TooltipComponent } = await import('echarts/components')
    expect(() => {
      echarts.use([GraphChart, TooltipComponent, CanvasRenderer])
    }).not.toThrow()
  })

  test('installed echarts package is major version 6', async () => {
    const pkg = await import('echarts/package.json', { assert: { type: 'json' } })
    expect(pkg.default.version.startsWith('6.')).toBe(true)
  })
})
