/**
 * useWorkbenchCheckpoint — 写作工作台检查点与差异对比
 *
 * 从 useCreatorWriteWorkbench 拆出，独立管理 checkpoint 快照和 diff 视图。
 * 依赖: chapterBodyDraft, selectedChapter, saveMessage (来自 deps)。
 *
 * @param {Object} deps
 * @param {import('vue').Ref<string>} deps.chapterBodyDraft - 章节草稿正文
 * @param {import('vue').Ref<number|null>} deps.selectedChapter - 当前选中章节
 * @param {import('vue').Ref<string>} deps.saveMessage - 保存状态消息
 * @returns {{
 *   checkpoints: import('vue').Ref<Array<{id:string,label:string,at:string,chapter:number|null,bodySnapshot:string}>>,
 *   diffCheckpointId: import('vue').Ref<string|null>,
 *   diffView: import('vue').ComputedRef<{checkpoint:Object,lines:Array<{type:string,text:string}>,changeCount:number}|null>,
 *   createCheckpoint: (label: string) => string,
 *   restoreCheckpoint: (id: string) => void,
 *   openCheckpointDiff: (id: string) => void,
 *   closeCheckpointDiff: () => void,
 * }}
 * 注意: 返回的 ref/computed 在 Pinia destructure 中不需要 .value
 */
import { computed, ref } from 'vue';
import type { Ref } from 'vue';
import { computeLineDiff, countDiffChanges } from '../utils/textDiffUtils.js';

interface Checkpoint {
  id: string;
  label: string;
  at: string;
  chapter: number | null;
  bodySnapshot: string;
}

interface DiffLine {
  type: 'same' | 'add' | 'remove';
  text: string;
}

interface DiffView {
  checkpoint: Checkpoint;
  lines: DiffLine[];
  changeCount: number;
}

interface CheckpointDeps {
  chapterBodyDraft: Ref<string>;
  selectedChapter: Ref<number | null>;
  saveMessage: Ref<string>;
}

export function useWorkbenchCheckpoint(deps: CheckpointDeps) {
  const { chapterBodyDraft, selectedChapter, saveMessage } = deps;

  const checkpoints = ref<Checkpoint[]>([]);
  const diffCheckpointId = ref<string | null>(null);

  const diffView = computed<DiffView | null>(() => {
    const cp = checkpoints.value.find((c) => c.id === diffCheckpointId.value);
    if (!cp) return null;
    const lines = computeLineDiff(cp.bodySnapshot, chapterBodyDraft.value) as DiffLine[];
    return {
      checkpoint: cp,
      lines,
      changeCount: countDiffChanges(lines),
    };
  });

  function createCheckpoint(label: string): string {
    const id = `cp-${Date.now()}`;
    checkpoints.value = [
      {
        id,
        label,
        at: new Date().toISOString(),
        chapter: selectedChapter.value,
        bodySnapshot: chapterBodyDraft.value,
      },
      ...checkpoints.value,
    ].slice(0, 6);
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