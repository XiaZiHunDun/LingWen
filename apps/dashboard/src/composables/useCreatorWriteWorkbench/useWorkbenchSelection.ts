/**
 * useWorkbenchSelection — 选区 + 控制参数（Phase 60.2）
 *
 * 从 useCreatorWriteWorkbench.js 拆出：bodySelection + captureBodySelection +
 * applyTextToSelection + hasBodySelection + styleStrength/selectionLocked/
 * allowWorldbuildingFill/goalTag + toggleSelectionLock + getControls。
 *
 * Agent statusLine 通过 deps 注入 getAgentStatusLine/setAgentStatusLine callback
 * （避免子模块直接 import useCreatorAgent）。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';

interface BodySelection {
  start: number;
  end: number;
  text: string;
}

export interface WorkbenchSelectionDeps {
  chapterBodyDraft: Ref<string>;
  saveMessage: Ref<string>;
  getAgentStatusLine?: () => Ref<string>;
  setAgentStatusLine?: (value: string) => void;
}

interface SelectionControls {
  styleStrength: number;
  selectionLocked: boolean;
  allowWorldbuildingFill: boolean;
  goalTag: string;
}

interface QualityHint {
  level: string;
  text: string;
  source?: string;
}

export interface WorkbenchSelectionReturn {
  bodySelection: Ref<BodySelection>;
  hasBodySelection: ComputedRef<boolean>;
  qualityHints: Ref<QualityHint[]>;
  styleStrength: Ref<number>;
  selectionLocked: Ref<boolean>;
  allowWorldbuildingFill: Ref<boolean>;
  goalTag: Ref<string>;
  captureBodySelection: (textarea: HTMLTextAreaElement | null) => void;
  applyTextToSelection: (text: string) => void;
  toggleSelectionLock: () => void;
  getControls: () => SelectionControls;
}

const EMPTY_SELECTION: BodySelection = { start: 0, end: 0, text: '' };
const LOCK_STATUS_MESSAGE = '选区已锁定，改写不会覆盖选中文字';
const EDITOR_WRITE_HINT = '已写入编辑器（未保存到磁盘）';

export function useWorkbenchSelection(
  deps: WorkbenchSelectionDeps,
): WorkbenchSelectionReturn {
  const { chapterBodyDraft, setAgentStatusLine } = deps;

  const bodySelection = ref<BodySelection>({ ...EMPTY_SELECTION });
  const qualityHints = ref<QualityHint[]>([]);
  const styleStrength = ref(1);
  const selectionLocked = ref(false);
  const allowWorldbuildingFill = ref(false);
  const goalTag = ref('');

  const hasBodySelection = computed(() => Boolean(bodySelection.value.text?.trim()));

  function captureBodySelection(textarea: HTMLTextAreaElement | null): void {
    if (!textarea || typeof textarea.selectionStart !== 'number') {
      bodySelection.value = { ...EMPTY_SELECTION };
      return;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = start !== end ? textarea.value.slice(start, end) : '';
    bodySelection.value = { start, end, text };
  }

  function applyTextToSelection(text: string): void {
    const sel = bodySelection.value;
    const draft = chapterBodyDraft.value;
    if (sel.text && sel.start !== sel.end) {
      chapterBodyDraft.value = draft.slice(0, sel.start) + text + draft.slice(sel.end);
    } else {
      chapterBodyDraft.value = draft ? `${draft}\n\n${text}` : text;
    }
    qualityHints.value = [
      { level: 'ok', text: EDITOR_WRITE_HINT },
    ];
  }

  function toggleSelectionLock(): void {
    selectionLocked.value = !selectionLocked.value;
    if (selectionLocked.value && hasBodySelection.value && setAgentStatusLine) {
      setAgentStatusLine(LOCK_STATUS_MESSAGE);
    }
  }

  function getControls(): SelectionControls {
    return {
      styleStrength: styleStrength.value,
      selectionLocked: selectionLocked.value,
      allowWorldbuildingFill: allowWorldbuildingFill.value,
      goalTag: goalTag.value,
    };
  }

  return {
    bodySelection,
    hasBodySelection,
    qualityHints,
    styleStrength,
    selectionLocked,
    allowWorldbuildingFill,
    goalTag,
    captureBodySelection,
    applyTextToSelection,
    toggleSelectionLock,
    getControls,
  };
}
