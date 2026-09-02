/**
 * batch-deviation.spec.ts — 批次差异纯推导工具（REQ-001 切片 C/E 共享）
 */
import { describe, expect, it } from 'vitest';
import {
  computeBatchRange,
  computeCompletedNums,
  computeBatchDeviations,
  buildBatchBand,
  padChapter,
} from '../../../src/utils/batchDeviation';

describe('batchDeviation utils', () => {
  it('padChapter 补零到三位', () => {
    expect(padChapter(3)).toBe('003');
    expect(padChapter(120)).toBe('120');
  });

  it('computeBatchRange 计算范围与总数', () => {
    expect(computeBatchRange(null)).toEqual({ start: 0, end: 0, total: 0 });
    expect(computeBatchRange({ start_chapter: 3, end_chapter: 6 })).toEqual({ start: 3, end: 6, total: 4 });
    // 结束小于开始 → total 0
    expect(computeBatchRange({ start_chapter: 6, end_chapter: 2 })).toEqual({ start: 6, end: 2, total: 0 });
  });

  it('computeCompletedNums 聚合完成章节集合', () => {
    const set = computeCompletedNums([{ chapter_num: 1 }, { chapter_num: 3 }, { chapter_num: 1 }]);
    expect([...set]).toEqual([1, 3]);
  });

  it('computeBatchDeviations 仅标记越序改定章', () => {
    const done = new Set([1, 3]);
    const devs = computeBatchDeviations(1, 4, done);
    expect(devs.map((d) => d.num)).toEqual([3]);
    expect(devs[0].text).toContain('ch003');
  });

  it('buildBatchBand 按状态生成节奏格', () => {
    const done = new Set([1, 3]);
    const deviating = new Set([3]);
    const band = buildBatchBand(1, 3, done, deviating);
    expect(band.map((c) => c.state)).toEqual(['done', 'pending', 'deviating']);
  });
});
