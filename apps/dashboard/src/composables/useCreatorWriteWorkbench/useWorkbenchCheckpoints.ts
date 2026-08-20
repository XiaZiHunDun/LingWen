/**
 * useWorkbenchCheckpoints — 检查点 + diff 视图（Phase 60.1）
 *
 * 从 useCreatorWriteWorkbench.js 拆出：checkpoints state + createCheckpoint +
 * restoreCheckpoint + openCheckpointDiff + closeCheckpointDiff + diffView computed。
 * 无跨域依赖、无 timer。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { computeLineDiff, countDiffChanges } from '../../utils/textDiffUtils.js';

export interface CheckpointEntry {
  id: string;
  label: string;
  at: string;
  chapter: number | null;
  bodySnapshot: string;
}

export interface DiffViewLine {
  type: string;
  text: string;
}

export interface DiffView {
  checkpoint: CheckpointEntry;
  lines: DiffViewLine[];
  changeCount: number;
}

export interface WorkbenchCheckpointsDeps {
  selectedChapter: Ref<number | null>;
  chapterBodyDraft: Ref<string>;
  saveMessage: Ref<string>;
}

export interface WorkbenchCheckpointsReturn {
  checkpoints: Ref<CheckpointEntry[]>;
  diffCheckpointId: Ref<string | null>;
  diffView: ComputedRef<DiffView | null>;
  createCheckpoint: (label: string) => string;
  restoreCheckpoint: (id: string) => void;
  openCheckpointDiff: (id: string) => void;
  closeCheckpointDiff: () => void;
}

const MAX_CHECKPOINTS = 6;

export function useWorkbenchCheckpoints(
  deps: WorkbenchCheckpointsDeps,
): WorkbenchCheckpointsReturn {
  const { selectedChapter, chapterBodyDraft, saveMessage } = deps;

  const checkpoints = ref<CheckpointEntry[]>([]);
  const diffCheckpointId = ref<string | null>(null);

  function createCheckpoint(label: string): string {
    const id = `cp-${Date.now()}`;
    const entry: CheckpointEntry = {
      id,
      label,
      at: new Date().toISOString(),
      chapter: selectedChapter.value,
      bodySnapshot: chapterBodyDraft.value,
    };
    checkpoints.value = [entry, ...checkpoints.value].slice(0, MAX_CHECKPOINTS);
    return id;
  }

  function restoreCheckpoint(id: string): void {
    const cp = checkpoints.value.find((c) => c.id === id);
    if (!cp) return;
    chapterBodyDraft.value = cp.bodySnapshot;
    saveMessage.value = `已恢复到 ${cp.label}`;
    diffCheckpointId.value = null;
  }

  function openCheckpointDiff(id: string): void {
    diffCheckpointId.value = id;
  }

  function closeCheckpointDiff(): void {
    diffCheckpointId.value = null;
  }

  const diffView = computed<DiffView | null>(() => {
    const cp = checkpoints.value.find((c) => c.id === diffCheckpointId.value);
    if (!cp) return null;
    const lines = computeLineDiff(cp.bodySnapshot, chapterBodyDraft.value);
    return {
      checkpoint: cp,
      lines,
      changeCount: countDiffChanges(lines),
    };
  });

  return {
    checkpoints,
    diffCheckpointId,
    diffView,
    createCheckpoint,
    restoreCheckpoint,
    openCheckpointDiff,
    closeCheckpointDiff,
  };
}
