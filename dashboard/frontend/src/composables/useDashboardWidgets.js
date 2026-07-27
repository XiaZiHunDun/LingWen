import { defineWidget, registerWidgets } from './useWidgetRegistry'

/**
 * 注册 Dashboard 常用 Widget
 */
export function registerDashboardWidgets() {
  // 统计卡片 Widget
  defineWidget('stats-card', {
    name: '统计卡片',
    component: () => import('../components/widgets/StatsWidget.vue'),
    category: 'analytics',
    description: '展示关键统计数据',
    width: 'large',
    height: 'medium',
    defaultProps: {
      title: '统计数据',
      stats: [],
      refreshable: false,
    },
  })

  // 图表 Widget
  defineWidget('chart-container', {
    name: '图表容器',
    component: () => import('../components/widgets/ChartWidget.vue'),
    category: 'analytics',
    description: '图表展示容器',
    width: 'full',
    height: 'large',
    defaultProps: {
      title: '图表',
      chartType: '',
    },
  })

  // 钩子趋势图 Widget
  defineWidget('hook-trend-chart', {
    name: '钩子趋势图',
    component: () => import('../components/HookTrendChart.vue'),
    category: 'charts',
    description: '展示钩子强度趋势',
    width: 'full',
    height: 'large',
    defaultProps: {
      data: [],
    },
  })

  // 爽点分布图 Widget
  defineWidget('coolpoint-chart', {
    name: '爽点分布图',
    component: () => import('../components/CoolpointChart.vue'),
    category: 'charts',
    description: '展示爽点分布情况',
    width: 'full',
    height: 'large',
    defaultProps: {
      data: [],
    },
  })

  // 章节表格 Widget
  defineWidget('chapter-table', {
    name: '章节表格',
    component: () => import('../components/ChapterTable.vue'),
    category: 'tables',
    description: '展示章节列表',
    width: 'full',
    height: 'medium',
    defaultProps: {
      chapters: [],
    },
  })

  // 成本趋势图 Widget
  defineWidget('cost-trend-chart', {
    name: '成本趋势图',
    component: () => import('../components/CostTrendChart.vue'),
    category: 'charts',
    description: '展示成本变化趋势',
    width: 'full',
    height: 'large',
    defaultProps: {},
  })

  // 成本柱状图 Widget
  defineWidget('cost-bar-chart', {
    name: '成本柱状图',
    component: () => import('../components/CostBarChart.vue'),
    category: 'charts',
    description: '展示成本对比',
    width: 'full',
    height: 'large',
    defaultProps: {},
  })

  // 评分雷达图 Widget
  defineWidget('score-radar-chart', {
    name: '评分雷达图',
    component: () => import('../components/ScoreRadarChart.vue'),
    category: 'charts',
    description: '展示多维评分',
    width: 'medium',
    height: 'medium',
    defaultProps: {},
  })

  // 冲击图 Widget
  defineWidget('impact-graph', {
    name: '冲击图',
    component: () => import('../components/ImpactGraph.vue'),
    category: 'graphs',
    description: '展示影响关系图',
    width: 'large',
    height: 'large',
    defaultProps: {},
  })

  // 级联图 Widget
  defineWidget('cascade-graph', {
    name: '级联图',
    component: () => import('../components/CascadeGraph.vue'),
    category: 'graphs',
    description: '展示级联关系',
    width: 'large',
    height: 'large',
    defaultProps: {},
  })

  // 工作流图 Widget
  defineWidget('workflow-graph', {
    name: '工作流图',
    component: () => import('../components/WorkflowGraph.vue'),
    category: 'graphs',
    description: '展示工作流',
    width: 'large',
    height: 'large',
    defaultProps: {},
  })
}

/**
 * 获取默认 Dashboard Widget 布局
 */
export function getDefaultDashboardLayout() {
  return [
    {
      id: 'overview-stats',
      widgetId: 'stats-card',
      props: { title: '追读力概览' },
      grid: { x: 0, y: 0, w: 2, h: 1 },
    },
    {
      id: 'hook-trend',
      widgetId: 'hook-trend-chart',
      props: {},
      grid: { x: 0, y: 1, w: 2, h: 2 },
    },
    {
      id: 'coolpoint-chart',
      widgetId: 'coolpoint-chart',
      props: {},
      grid: { x: 0, y: 3, w: 2, h: 2 },
    },
    {
      id: 'chapter-table',
      widgetId: 'chapter-table',
      props: {},
      grid: { x: 0, y: 5, w: 2, h: 2 },
    },
  ]
}
