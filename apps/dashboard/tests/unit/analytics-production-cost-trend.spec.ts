import { describe, it, expect } from 'vitest';
import {
  buildCostTrendChartOption,
  formatTrendAxisLabel,
  hasCostTrendData,
  productionCostTrendSummaryLines,
} from '../../src/utils/analyticsProductionCostTrend.js';

describe('analyticsProductionCostTrend', () => {
  const trend = {
    point_count: 2,
    total_cost_usd: 0.5,
    points: [
      {
        recorded_at: '2026-06-01T10:00:00Z',
        record_id: 'r1',
        record_type: 'pilot',
        label: '第一章',
        cost_usd: 0.2,
        incremental_cost_usd: 0.2,
        cumulative_cost_usd: 0.2,
      },
      {
        recorded_at: null,
        record_id: 'r2',
        record_type: 'batch',
        label: '批量',
        cost_usd: 0.3,
        incremental_cost_usd: 0.3,
        cumulative_cost_usd: 0.5,
      },
    ],
  };

  it('hasCostTrendData guards empty input', () => {
    expect(hasCostTrendData(null)).toBe(false);
    expect(hasCostTrendData({ points: [], point_count: 0, total_cost_usd: 0 })).toBe(false);
    expect(hasCostTrendData(trend)).toBe(true);
  });

  it('formatTrendAxisLabel prefers date then label', () => {
    expect(formatTrendAxisLabel(trend.points[0])).toBe('2026-06-01');
    expect(formatTrendAxisLabel(trend.points[1])).toBe('批量');
    expect(formatTrendAxisLabel({ record_id: 'x', record_type: 'pilot', label: 'x', incremental_cost_usd: 0, cumulative_cost_usd: 0 })).toBe('x');
  });

  it('buildCostTrendChartOption returns empty object without points', () => {
    expect(buildCostTrendChartOption(null)).toEqual({});
  });

  it('buildCostTrendChartOption builds series and tooltip formatter', () => {
    const option = buildCostTrendChartOption(trend) as {
      xAxis: { data: string[] };
      series: unknown[];
      tooltip: { formatter: (items: Array<{ dataIndex: number }>) => string };
    };
    expect(option.series).toHaveLength(2);
    expect(option.xAxis.data).toEqual(['2026-06-01', '批量']);
    const html = option.tooltip.formatter([{ dataIndex: 0 }]);
    expect(html).toContain('当次');
    expect(html).toContain('类型: pilot');
    expect(option.tooltip.formatter([{ dataIndex: 99 }])).toBe('');
  });

  it('productionCostTrendSummaryLines summarizes last point', () => {
    expect(productionCostTrendSummaryLines(null)).toEqual([]);
    const lines = productionCostTrendSummaryLines(trend);
    expect(lines[0]).toContain('时间序列 2 点');
    expect(lines[1]).toContain('最近: 批量');
  });
});
