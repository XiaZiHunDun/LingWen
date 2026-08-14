/**
 * useWriteFlow — 写作流（选章节/保存正文/保存大纲/自动保存/记忆同步）
 *
 * Phase 19 Task 5 占位：useCreatorWrite.js 599 行拆为 3 子模块之一。
 * 负责: selectedChapter + chapterBodyDraft + selectChapter + jumpToChapter +
 *       saveChapterBody + saveChapterOutline + autoSaveChapterBody +
 *       syncMemoryAssets + bindChapterBodyTextareaRef + maybeAutoSelectWritingChapter。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface WriteFlowDeps {
  // 暂未使用（待后续会话填充）
}

export interface WriteFlowReturn {
  selectedChapter: Ref<number | null>;
  chapterBodyDraft: Ref<string>;
  chapterOutlineDraft: Ref<string>;
  chapterBodySaving: Ref<boolean>;
  chapterOutlineSaving: Ref<boolean>;
  chapterBodyAutoSavedAt: Ref<Date | null>;
  selectChapter: (chapter: number) => Promise<void>;
  jumpToChapter: (chapter: number) => Promise<void>;
  saveChapterBody: () => Promise<void>;
  saveChapterOutline: () => Promise<void>;
  autoSaveChapterBody: () => Promise<void>;
  syncMemoryAssets: (items: Array<Record<string, unknown>>) => void;
  bindChapterBodyTextareaRef: (el: HTMLElement | null) => void;
  maybeAutoSelectWritingChapter: () => void;
}

// 占位实现 — 后续会话填充实际逻辑
export function useWriteFlow(_deps: WriteFlowDeps): WriteFlowReturn {
  throw new Error('useWriteFlow: not yet implemented (Phase 19 Task 5.1)');
}