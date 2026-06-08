// tests/unit/setup.ts — Phase 8.30
// vitest 全局 setup: stub echarts module 绕过 jsdom canvas 限制
// 5 个 ECharts 组件 (CostBarChart / CostTrendChart / ScoreRadarChart / HookTrendChart
// / CoolpointChart) 内部走 zrender.Painter 渲染到 HTMLCanvasElement.getContext('2d'),
// jsdom 不实现 → clearRect null deref. 完整支持是 ceremonial Playwright 的事.
// vitest 只关 component-level 行为契约 (props / emit / class / aria / data-testid),
// 不需真实 pixel 渲染. stub 让 chart 走空壳 init/setOption/dispose 即可.
import { vi } from 'vitest'

vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    clear: vi.fn(),
    dispose: vi.fn(),
    resize: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  })),
  // ECharts 5.x 还有 named export (getInstanceByDom / connect / disconnect) — 也 stub 防 import 报错
  getInstanceByDom: vi.fn(() => null),
  connect: vi.fn(),
  disconnect: vi.fn(),
  registerTheme: vi.fn(),
}))
