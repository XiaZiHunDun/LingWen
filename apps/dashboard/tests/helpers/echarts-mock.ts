import { vi } from 'vitest'
import type { EChartsType } from 'echarts'

/** Minimal ECharts instance stub for component unit tests (jsdom has no canvas). */
export function createMockEChartsInstance(setOptionSpy = vi.fn()): EChartsType {
  return {
    setOption: setOptionSpy,
    clear: vi.fn(),
    dispose: vi.fn(),
    resize: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  } as unknown as EChartsType
}
