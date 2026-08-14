/**
 * useWriteTools — 写作工具（format/label/class/highlight/scroll/batch inline summary）
 *
 * Phase 19 Task 5 占位：useCreatorWrite.js 599 行拆为 3 子模块之一。
 * 负责: formatBodySaveTime + chapterRowClass + chapterVolumeLabel + chapterRowTitle +
 *       pulseChapterBodyHighlight + focusIssueParagraph +
 *       batchDeviationsInRange + scrollToBatchDeviationList +
 *       openFirstBatchDeviationChapter + updateBatchDeviationInlineSummary +
 *       linkBatchDeviationInlineSummary + dismissBatchDeviationInlineSummary +
 *       navigateIssueList。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
export interface WriteToolsDeps {
  // 暂未使用（待后续会话填充）
}

export interface WriteToolsReturn {
  formatBodySaveTime: (date: Date | null) => string;
  chapterRowClass: (chapter: Record<string, unknown>) => string;
  chapterVolumeLabel: (chapter: Record<string, unknown>) => string;
  chapterRowTitle: (chapter: Record<string, unknown>) => string;
  pulseChapterBodyHighlight: (issueIdx: number, source?: string) => void;
  focusIssueParagraph: (issue: Record<string, unknown>, issueIdx: number, source?: string) => void;
  batchDeviationsInRange: (start: number, end: number) => Array<Record<string, unknown>>;
  scrollToBatchDeviationList: (start: number, end: number) => Promise<void>;
  openFirstBatchDeviationChapter: (start: number, end: number) => Promise<void>;
  updateBatchDeviationInlineSummary: (start: number, end: number) => void;
  linkBatchDeviationInlineSummary: (start: number, end: number) => Promise<void>;
  dismissBatchDeviationInlineSummary: () => void;
  navigateIssueList: (
    event: KeyboardEvent,
    issues: Array<Record<string, unknown>>,
    currentIdx: number,
    onSelect: (issue: Record<string, unknown>, idx: number) => void,
    testIdPrefix: string,
  ) => void;
}

// 占位实现 — 后续会话填充实际逻辑
export function useWriteTools(_deps: WriteToolsDeps): WriteToolsReturn {
  throw new Error('useWriteTools: not yet implemented (Phase 19 Task 5.3)');
}