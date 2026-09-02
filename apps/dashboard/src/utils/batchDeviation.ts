/**
 * batchDeviation.ts — 批次「差异/偏差」纯推导工具（REQ-001 切片 C/E 共享）
 *
 * 从批次起始/结束章节与完成事件，推导：
 * - 批次范围与总数
 * - 已完成章节集合
 * - 越序改定偏差（前序章节尚未完成就已改定的章）
 * - 节奏带格子（done / deviating / pending）
 *
 * 纯函数，无副作用，供节奏带（只读）与差异收尾（可操作）复用。
 */

export interface BatchJobLite {
  start_chapter?: number | null;
  end_chapter?: number | null;
}

export interface BatchEventLite {
  chapter_num?: number | null;
}

export interface BatchRange {
  start: number;
  end: number;
  total: number;
}

export interface BatchDeviation {
  num: number;
  text: string;
}

export interface BatchRhythmCell {
  num: number;
  state: 'done' | 'deviating' | 'pending';
  title: string;
}

export function padChapter(n: number): string {
  return String(n).padStart(3, '0');
}

export function computeBatchRange(job: BatchJobLite | null): BatchRange {
  if (!job) return { start: 0, end: 0, total: 0 };
  const start = Number(job.start_chapter ?? 0);
  const end = Number(job.end_chapter ?? start);
  const total = end >= start ? end - start + 1 : 0;
  return { start, end, total };
}

export function computeCompletedNums(events: readonly BatchEventLite[]): Set<number> {
  const set = new Set<number>();
  for (const ev of events) {
    if (typeof ev.chapter_num === 'number') set.add(ev.chapter_num);
  }
  return set;
}

/** 越序偏差：某章已完成，但其前序（范围内、编号更小）章节仍未完成。 */
export function computeBatchDeviations(
  start: number,
  end: number,
  completed: ReadonlySet<number>,
): BatchDeviation[] {
  const list: BatchDeviation[] = [];
  for (let num = start; num <= end; num += 1) {
    if (!completed.has(num)) continue;
    let jumpAhead = false;
    for (let m = start; m < num; m += 1) {
      if (!completed.has(m)) {
        jumpAhead = true;
        break;
      }
    }
    if (jumpAhead) {
      list.push({ num, text: `ch${padChapter(num)} 在前序章节完成前已改定` });
    }
  }
  return list;
}

export function computeBatchDeviatingNums(deviations: readonly BatchDeviation[]): Set<number> {
  return new Set(deviations.map((d) => d.num));
}

export function buildBatchBand(
  start: number,
  end: number,
  completed: ReadonlySet<number>,
  deviating: ReadonlySet<number>,
): BatchRhythmCell[] {
  const cells: BatchRhythmCell[] = [];
  for (let num = start; num <= end; num += 1) {
    let state: BatchRhythmCell['state'] = 'pending';
    if (completed.has(num)) state = deviating.has(num) ? 'deviating' : 'done';
    cells.push({ num, state, title: `ch${padChapter(num)}（${state}）` });
  }
  return cells;
}
