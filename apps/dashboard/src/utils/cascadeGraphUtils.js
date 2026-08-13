/**
 * cascadeGraphUtils.js — CascadeGraph view modes (Phase 9.51 F40)
 * View 1: force (default, Phase 9.15)
 * View 2: depth-layer — nodes positioned/colored by BFS depth
 * View 3: action-cluster — nodes grouped/colored by cascade action type
 */

/** @typedef {'force'|'depth-layer'|'action-cluster'} CascadeViewModeT */

/** @type {CascadeViewModeT[]} */
export const CASCADE_VIEW_MODES = ['force', 'depth-layer', 'action-cluster'];

export const CASCADE_VIEW_MODE_LABELS = {
  force: 'Force',
  'depth-layer': 'Depth',
  'action-cluster': 'Action',
};

export const DEPTH_LAYER_COLORS = {
  0: '#6366f1',
  1: '#3b82f6',
  2: '#06b6d4',
  3: '#14b8a6',
};

export const ACTION_TYPE_COLORS = {
  trigger: '#22c55e',
  propagate: '#3b82f6',
  modify: '#eab308',
  unknown: '#9ca3af',
};

export const ACTION_TYPE_ORDER = ['trigger', 'propagate', 'modify', 'unknown'];

/**
 * @param {Array<{ id: string }>} nodes
 * @param {Array<{ action?: string, from?: string, to?: string, depth?: number }>} actions
 * @returns {Record<string, number>}
 */
export function computeNodeDepthMap(nodes, actions) {
  /** @type {Record<string, number>} */
  const depths = {};
  for (const n of nodes) {
    depths[n.id] = 1;
  }
  for (const a of actions) {
    const d = typeof a.depth === 'number' ? a.depth : 1;
    if (a.to) {
      depths[a.to] = Math.max(depths[a.to] ?? 0, d);
    }
    if (a.from) {
      const fromDepth = Math.max(0, d - 1);
      depths[a.from] = depths[a.from] !== undefined
        ? Math.min(depths[a.from], fromDepth)
        : fromDepth;
    }
  }
  return depths;
}

/**
 * @param {Array<{ action?: string, from?: string, to?: string }>} actions
 * @returns {Record<string, string>}
 */
export function computeNodeActionMap(actions) {
  /** @type {Record<string, string>} */
  const map = {};
  for (const a of actions) {
    const act = a.action || 'propagate';
    if (a.to) map[a.to] = act;
    if (a.from && map[a.from] === undefined) map[a.from] = 'trigger';
  }
  return map;
}

/**
 * @param {string} action
 * @param {boolean} dryRun
 * @returns {string}
 */
export function actionNodeColor(action, dryRun = false) {
  if (dryRun) {
    if (action === 'trigger') return ACTION_TYPE_COLORS.trigger;
    if (action === 'modify') return ACTION_TYPE_COLORS.modify;
    return ACTION_TYPE_COLORS.unknown;
  }
  return ACTION_TYPE_COLORS[action] ?? ACTION_TYPE_COLORS.unknown;
}

/**
 * @param {number} depth
 * @returns {string}
 */
export function depthLayerColor(depth) {
  return DEPTH_LAYER_COLORS[depth] ?? DEPTH_LAYER_COLORS[3];
}

/**
 * Assign fixed x/y for depth-layer layout (columns by depth).
 * @param {Array<{ id: string }>} nodes
 * @param {Record<string, number>} depthMap
 */
export function layoutNodesByDepth(nodes, depthMap) {
  /** @type {Record<number, number>} */
  const rowByDepth = {};
  return nodes.map((n) => {
    const depth = depthMap[n.id] ?? 1;
    const row = rowByDepth[depth] ?? 0;
    rowByDepth[depth] = row + 1;
    return {
      ...n,
      x: depth * 140,
      y: row * 60 + 20,
    };
  });
}

/**
 * Assign fixed x/y for action-cluster layout (columns by action type).
 * @param {Array<{ id: string }>} nodes
 * @param {Record<string, string>} actionMap
 */
export function layoutNodesByActionCluster(nodes, actionMap) {
  /** @type {Record<string, number>} */
  const rowByAction = {};
  return nodes.map((n) => {
    const action = actionMap[n.id] ?? 'unknown';
    const col = Math.max(0, ACTION_TYPE_ORDER.indexOf(action));
    const row = rowByAction[action] ?? 0;
    rowByAction[action] = row + 1;
    return {
      ...n,
      x: col * 160 + 40,
      y: row * 60 + 20,
    };
  });
}

/**
 * Build ECharts graph nodes + layout config for a cascade payload.
 * @param {object|null} cascade
 * @param {CascadeViewModeT} viewMode
 * @param {boolean} dryRun
 */
export function buildCascadeGraphSeriesData(cascade, viewMode, dryRun = false) {
  const rawNodes = (cascade?.cascade_nodes || []).slice(0, 100);
  const edges = (cascade?.cascade_edges || []).map((e) => ({
    source: e.from_node_id,
    target: e.to_node_id,
    lineStyle: { opacity: e.weight ?? 0.6 },
  }));
  const actions = cascade?.cascade_actions || [];
  const depthMap = computeNodeDepthMap(rawNodes, actions);
  const actionMap = computeNodeActionMap(actions);

  const baseNodes = rawNodes.map((n) => ({
    id: n.id,
    name: `${n.id} (V${n.volume}c${n.chapter})`,
    symbolSize: 30,
    raw: n,
  }));

  if (viewMode === 'depth-layer') {
    const positioned = layoutNodesByDepth(baseNodes, depthMap);
    const nodes = positioned.map((n) => ({
      id: n.id,
      name: n.name,
      symbolSize: n.symbolSize,
      x: n.x,
      y: n.y,
      itemStyle: { color: depthLayerColor(depthMap[n.id] ?? 1) },
    }));
    return { layout: 'none', nodes, edges };
  }

  if (viewMode === 'action-cluster') {
    const positioned = layoutNodesByActionCluster(baseNodes, actionMap);
    const nodes = positioned.map((n) => {
      const action = actionMap[n.id] ?? 'unknown';
      return {
        id: n.id,
        name: n.name,
        symbolSize: n.symbolSize,
        x: n.x,
        y: n.y,
        itemStyle: { color: actionNodeColor(action, dryRun) },
        category: action,
      };
    });
    return { layout: 'none', nodes, edges };
  }

  // force layout (default)
  const nodes = baseNodes.map((n) => {
    const action = actionMap[n.id] ?? 'trigger';
    const color = dryRun ? actionNodeColor(action, true) : '#3b82f6';
    return {
      id: n.id,
      name: n.name,
      symbolSize: n.symbolSize,
      itemStyle: { color },
    };
  });
  return { layout: 'force', nodes, edges };
}

/**
 * @param {object|null} cascade
 * @param {CascadeViewModeT} viewMode
 * @param {boolean} dryRun
 */
export function buildCascadeChartOption(cascade, viewMode, dryRun = false) {
  const { layout, nodes, edges } = buildCascadeGraphSeriesData(cascade, viewMode, dryRun);
  const depth = cascade?.depth_reached ?? 0;
  const modeLabel = CASCADE_VIEW_MODE_LABELS[viewMode] ?? viewMode;
  return {
    title: { text: `Cascade (${modeLabel}, depth ${depth})`, left: 'center' },
    tooltip: {},
    series: [{
      type: 'graph',
      layout,
      roam: true,
      data: nodes,
      edges,
      force: layout === 'force' ? { repulsion: 100 } : undefined,
      emphasis: {
        focus: 'self',
        itemStyle: { opacity: 1.0, borderColor: '#1e40af', borderWidth: 2 },
      },
      select: { itemStyle: { opacity: 0.3 } },
    }],
  };
}
