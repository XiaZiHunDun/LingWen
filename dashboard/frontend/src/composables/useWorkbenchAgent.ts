/**
 * useWorkbenchAgent — 写作工作台 Agent 控制与生成管理
 *
 * 从 useCreatorWriteWorkbench 拆出，独立管理 Agent 控制参数和生成流程。
 * 依赖: uiProfile, bodySelection, selectedChapter, chapterBodyDraft,
 *       getControls, applyTextToSelection, createCheckpoint, restoreCheckpoint,
 *       focusParagraphByIndex (来自 deps)。
 *
 * @param {Object} deps
 * @param {import('vue').ComputedRef<Record<string,unknown>>} deps.uiProfile
 * @param {import('vue').Ref<{start:number,end:number,text:string}>} deps.getSelection
 * @param {() => number|null} deps.getChapterNum
 * @param {() => string} deps.getBodyDraft
 * @param {() => {styleStrength:number,selectionLocked:boolean,allowWorldbuildingFill:boolean,goalTag:string}} deps.getControls
 * @param {(text: string) => void} deps.applyTextToSelection
 * @param {(label: string) => string} deps.createCheckpoint
 * @param {(id: string) => void} deps.restoreCheckpoint
 * @param {(paragraph: number) => void} [deps.onAnnotationFocus]
 * @param {import('vue').Ref<string>} deps.intentText
 * @returns {{
 *   agent: {generating: import('vue').Ref<boolean>,candidates: import('vue').Ref<Array<{id?:string,label?:string,text?:string}>>,directorAdvice: import('vue').Ref<Array<{id?:string,text?:string}>>,statusLine: import('vue').Ref<string>,runPlan: (action: string, actionLabel: string, pathMeta?: unknown) => Promise<void>},
 *   generateIntensity: import('vue').Ref<string>,
 *   generateRunning: import('vue').Ref<boolean>,
 *   styleStrength: import('vue').Ref<number>,
 *   selectionLocked: import('vue').Ref<boolean>,
 *   allowWorldbuildingFill: import('vue').Ref<boolean>,
 *   goalTag: import('vue').Ref<string>,
 *   toggleSelectionLock: () => void,
 *   startQuickWrite: (actionLabel?: string|null) => Promise<void>,
 *   stopGenerate: () => void,
 * }}
 * 注意: 返回的 ref/computed 在 Pinia destructure 中不需要 .value
 */
import { ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { useCreatorAgent } from './useCreatorAgent.js';

interface AgentState {
  generating: Ref<boolean>;
  candidates: Ref<Array<{ id?: string; label?: string; text?: string }>>;
  directorAdvice: Ref<Array<{ id?: string; text?: string }>>;
  statusLine: Ref<string>;
  runPlan: (action: string, actionLabel: string, pathMeta?: unknown) => Promise<void>;
}

interface AgentControls {
  styleStrength: number;
  selectionLocked: boolean;
  allowWorldbuildingFill: boolean;
  goalTag: string;
}

interface BodySelection {
  start: number;
  end: number;
  text: string;
}

interface AgentDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  getSelection: () => BodySelection;
  getChapterNum: () => number | null;
  getBodyDraft: () => string;
  applyTextToSelection: (text: string) => void;
  createCheckpoint: (label: string) => string;
  restoreCheckpoint: (id: string) => void;
  onAnnotationFocus?: (paragraph: number) => void;
  intentText: Ref<string>;
  qualityHints: Ref<Array<{ level: string; text: string; source?: string }>>;
  hasBodySelection: Ref<boolean>;
}

export function useWorkbenchAgent(deps: AgentDeps) {
  const {
    uiProfile,
    getSelection,
    getChapterNum,
    getBodyDraft,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint,
    onAnnotationFocus,
    intentText,
    qualityHints,
    hasBodySelection,
  } = deps;

  const generateIntensity = ref<string>('balanced');
  const generateRunning = ref<boolean>(false);

  const styleStrength = ref<number>(1);
  const selectionLocked = ref<boolean>(false);
  const allowWorldbuildingFill = ref<boolean>(false);
  const goalTag = ref<string>('');

  function getControls(): AgentControls {
    return {
      styleStrength: styleStrength.value,
      selectionLocked: selectionLocked.value,
      allowWorldbuildingFill: allowWorldbuildingFill.value,
      goalTag: goalTag.value,
    };
  }

  const agent: AgentState = useCreatorAgent({
    uiProfile,
    getSelection,
    getChapterNum,
    getBodyDraft,
    getControls,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint: (id: string) => restoreCheckpoint(id),
    onAnnotationFocus: (paragraph: number) => {
      if (onAnnotationFocus) onAnnotationFocus(paragraph);
    },
  }) as unknown as AgentState;

  async function startQuickWrite(actionLabel: string | null = null): Promise<void> {
    if (!intentText.value.trim()) {
      qualityHints.value = [{ level: 'warn', text: '可先输入一句话意图，或直接在正文区开写' }];
      return;
    }
    generateRunning.value = true;
    try {
      const label = actionLabel || `一键开写：${intentText.value.trim()}`;
      await agent.runPlan('quick-write', label);
      if (!agent.candidates.value.length && !agent.directorAdvice.value.length) {
        return;
      }
      qualityHints.value = [{ level: 'info', text: '从左侧或下方选择候选，确认后写入正文' }];
    } finally {
      generateRunning.value = false;
    }
  }

  function stopGenerate(): void {
    generateRunning.value = false;
    agent.generating.value = false;
    agent.statusLine.value = '已停止';
  }

  function toggleSelectionLock(): void {
    selectionLocked.value = !selectionLocked.value;
    if (selectionLocked.value && hasBodySelection.value) {
      agent.statusLine.value = '选区已锁定，改写不会覆盖选中文字';
    }
  }

  return {
    agent,
    generateIntensity,
    generateRunning,
    styleStrength,
    selectionLocked,
    allowWorldbuildingFill,
    goalTag,
    toggleSelectionLock,
    startQuickWrite,
    stopGenerate,
  };
}