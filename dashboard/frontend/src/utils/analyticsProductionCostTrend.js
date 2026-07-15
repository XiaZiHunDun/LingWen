/**
 * Phase 9.96 F87: production cost trend helpers for Analytics mini chart.
 */

/**
 * @typedef {Object} ProductionCostTrendPoint
 * @property {string|null} [recorded_at]
 * @property {string} record_id
 * @property {string} record_type
 * @property {string} label
 * @property {number|null} [cost_usd]
 * @property {number} incremental_cost_usd
 * @property {number} cumulative_cost_usd
 */

/**
 * @typedef {Object} ProductionCostTrend
 * @property {number} point_count
 * @property {number} total_cost_usd
 * @property {ProductionCostTrendPoint[]} points
 */

/**
 * @param {ProductionCostTrend|null|undefined} trend
 * @returns {boolean}
 */
export function hasCostTrendData(trend) {
  return Array.isArray(trend?.points) && trend.points.length > 0;
}

/**
 * @param {ProductionCostTrendPoint} point
 * @returns {string}
 */
export function formatTrendAxisLabel(point) {
  if (point?.recorded_at) {
    return point.recorded_at.slice(0, 10);
  }
  return point?.label || point?.record_id || '-';
}

/**
 * @param {ProductionCostTrend|null|undefined} trend
 * @returns {import('echarts').EChartsOption}
 */
export function buildCostTrendChartOption(trend) {
  const points = trend?.points ?? [];
  if (!points.length) {
    return {};
  }

  const categories = points.map((p) => formatTrendAxisLabel(p));
  const incremental = points.map((p) => Number(p.incremental_cost_usd ?? 0));
  const cumulative = points.map((p) => Number(p.cumulative_cost_usd ?? 0));

  const pixelText = {
    fontFamily: 'Press Start 2P',
    fontSize: 8,
    color: '#2a220f',
  };

  return {
    grid: { top: 36, right: 48, bottom: 48, left: 52 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#2a220f',
      borderColor: '#2a220f',
      borderWidth: 2,
      textStyle: { ...pixelText, color: '#fff7e8' },
      formatter: (items) => {
        const idx = items?.[0]?.dataIndex ?? 0;
        const p = points[idx];
        if (!p) return '';
        const lines = [
          p.label,
          `当次: $${Number(p.incremental_cost_usd ?? 0).toFixed(4)}`,
          `累计: $${Number(p.cumulative_cost_usd ?? 0).toFixed(4)}`,
        ];
        if (p.record_type) lines.push(`类型: ${p.record_type}`);
        return lines.join('<br/>');
      },
    },
    legend: {
      data: ['当次成本', '累计成本'],
      textStyle: pixelText,
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { ...pixelText, fontSize: 6, rotate: 35 },
      axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
    },
    yAxis: [
      {
        type: 'value',
        name: 'USD',
        nameTextStyle: pixelText,
        axisLabel: pixelText,
        axisLine: { lineStyle: { color: '#2a220f', width: 2 } },
        splitLine: { lineStyle: { color: '#2a220f', type: 'dashed', opacity: 0.35 } },
      },
      {
        type: 'value',
        name: '累计',
        show: false,
      },
    ],
    series: [
      {
        name: '当次成本',
        type: 'bar',
        data: incremental,
        itemStyle: { color: '#26a8ff', borderColor: '#2a220f', borderWidth: 1 },
      },
      {
        name: '累计成本',
        type: 'line',
        data: cumulative,
        smooth: false,
        symbol: 'square',
        symbolSize: 6,
        lineStyle: { color: '#ff9f43', width: 2 },
        itemStyle: { color: '#ff9f43', borderColor: '#2a220f', borderWidth: 1 },
      },
    ],
  };
}

/**
 * @param {ProductionCostTrend|null|undefined} trend
 * @returns {string[]}
 */
export function productionCostTrendSummaryLines(trend) {
  if (!hasCostTrendData(trend)) return [];
  const lastPoint = trend.points[trend.points.length - 1];
  return [
    `时间序列 ${trend.point_count} 点 · 累计 $${Number(trend.total_cost_usd ?? 0).toFixed(4)}`,
    lastPoint?.recorded_at
      ? `最近: ${lastPoint.recorded_at.slice(0, 19)} · ${lastPoint.label}`
      : `最近: ${lastPoint?.label ?? '-'}`,
  ];
}
