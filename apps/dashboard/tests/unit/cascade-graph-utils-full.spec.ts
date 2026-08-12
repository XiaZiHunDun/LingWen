// tests/unit/cascade-graph-utils-full.spec.ts — Phase 9.57 F48 branch boost
import { describe, test, expect } from 'vitest'
import {
  CASCADE_VIEW_MODES,
  computeNodeDepthMap,
  computeNodeActionMap,
  actionNodeColor,
  depthLayerColor,
  layoutNodesByDepth,
  layoutNodesByActionCluster,
  buildCascadeGraphSeriesData,
  buildCascadeChartOption,
} from '../../src/utils/cascadeGraphUtils.js'

const nodes = [{ id: 'a' }, { id: 'b' }, { id: 'c' }]
const actions = [
  { action: 'propagate', from: 'a', to: 'b', depth: 2 },
  { action: 'modify', from: 'b', to: 'c', depth: 3 },
]
const cascade = {
  cascade_nodes: [
    { id: 'a', volume: 1, chapter: 1 },
    { id: 'b', volume: 1, chapter: 2 },
    { id: 'c', volume: 2, chapter: 3 },
  ],
  cascade_edges: [{ from_node_id: 'a', to_node_id: 'b', weight: 0.8 }],
  cascade_actions: actions,
  depth_reached: 3,
}

describe('cascadeGraphUtils full coverage (F48)', () => {
  test('CASCADE_VIEW_MODES canonical', () => {
    expect(CASCADE_VIEW_MODES).toHaveLength(3)
  })

  test('computeNodeDepthMap assigns depths', () => {
    const map = computeNodeDepthMap(nodes, actions)
    expect(map.b).toBeGreaterThanOrEqual(2)
    expect(map.c).toBe(3)
  })

  test('computeNodeActionMap trigger and propagate', () => {
    const map = computeNodeActionMap(actions)
    expect(map.a).toBe('trigger')
    expect(map.b).toBe('propagate')
  })

  test('actionNodeColor dryRun branches', () => {
    expect(actionNodeColor('trigger', true)).toBe('#22c55e')
    expect(actionNodeColor('modify', true)).toBe('#eab308')
    expect(actionNodeColor('other', true)).toBe('#9ca3af')
    expect(actionNodeColor('propagate', false)).toBe('#3b82f6')
    expect(actionNodeColor('missing', false)).toBe('#9ca3af')
  })

  test('depthLayerColor fallback', () => {
    expect(depthLayerColor(1)).toBe('#3b82f6')
    expect(depthLayerColor(99)).toBe('#14b8a6')
  })

  test('layoutNodesByDepth and layoutNodesByActionCluster', () => {
    const depthMap = computeNodeDepthMap(nodes, actions)
    const actionMap = computeNodeActionMap(actions)
    const byDepth = layoutNodesByDepth(nodes, depthMap)
    const byAction = layoutNodesByActionCluster(nodes, actionMap)
    expect(byDepth[0].x).toBeDefined()
    expect(byAction[0].y).toBeDefined()
  })

  test('buildCascadeGraphSeriesData force mode', () => {
    const data = buildCascadeGraphSeriesData(cascade, 'force', false)
    expect(data.layout).toBe('force')
    expect(data.nodes.length).toBe(3)
  })

  test('buildCascadeGraphSeriesData depth-layer mode', () => {
    const data = buildCascadeGraphSeriesData(cascade, 'depth-layer', false)
    expect(data.layout).toBe('none')
    expect(data.nodes[0].itemStyle.color).toBeTruthy()
  })

  test('buildCascadeGraphSeriesData action-cluster dryRun', () => {
    const data = buildCascadeGraphSeriesData(cascade, 'action-cluster', true)
    expect(data.nodes.length).toBe(3)
    expect(data.nodes[0].category).toBeTruthy()
  })

  test('buildCascadeGraphSeriesData null cascade', () => {
    const data = buildCascadeGraphSeriesData(null, 'force', false)
    expect(data.nodes).toEqual([])
  })

  test('buildCascadeChartOption titles', () => {
    const opt = buildCascadeChartOption(cascade, 'depth-layer', false)
    expect(opt.title.text).toContain('Depth')
    const forceOpt = buildCascadeChartOption(cascade, 'force', true)
    expect(forceOpt.series[0].force).toBeTruthy()
  })
})
