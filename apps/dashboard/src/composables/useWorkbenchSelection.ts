/**
 * useWorkbenchSelection — 写作工作台选区与 Intent 管理
 *
 * 从 useCreatorWriteWorkbench 拆出，独立管理选区状态和创作意图。
 * 依赖: 无外部依赖，纯内部状态管理。
 *
 * @returns {{
 *   bodySelection: import('vue').Ref<{start:number,end:number,text:string}>,
 *   hasBodySelection: import('vue').ComputedRef<boolean>,
 *   captureBodySelection: (textarea: {selectionStart:number,selectionEnd:number,value:string}) => void,
 *   intentText: import('vue').Ref<string>,
 *   intentGenre: import('vue').Ref<string>,
 *   intentMood: import('vue').Ref<string>,
 *   intentType: import('vue').Ref<string>,
 *   intentTheme: import('vue').Ref<string>,
 *   intentHistory: import('vue').Ref<Array<{id:string,text:string,mood:string,type:string,theme:string,timestamp:string}>>,
 *   saveIntentToHistory: () => void,
 *   loadIntentFromHistory: (intent: {id:string,text:string,mood:string,type:string,theme:string,timestamp:string}) => void,
 *   clearIntentHistory: () => void,
 * }}
 * 注意: 返回的 ref/computed 在 Pinia destructure 中不需要 .value
 */
import { ref } from 'vue';

interface BodySelection {
  start: number;
  end: number;
  text: string;
}

interface IntentEntry {
  id: string;
  text: string;
  mood: string;
  type: string;
  theme: string;
  timestamp: string;
}

interface TextSelectionLike {
  selectionStart: number;
  selectionEnd: number;
  value: string;
}

export function useWorkbenchSelection() {
  const bodySelection = ref<BodySelection>({ start: 0, end: 0, text: '' });
  const intentText = ref<string>('');
  const intentGenre = ref<string>('');
  const intentMood = ref<string>('');
  const intentType = ref<string>('');
  const intentTheme = ref<string>('');
  const intentHistory = ref<IntentEntry[]>([]);

  function captureBodySelection(textarea: TextSelectionLike): void {
    if (!textarea || typeof textarea.selectionStart !== 'number') {
      bodySelection.value = { start: 0, end: 0, text: '' };
      return;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = start !== end ? textarea.value.slice(start, end) : '';
    bodySelection.value = { start, end, text };
  }

  function saveIntentToHistory(): void {
    if (!intentText.value.trim()) return;
    const intent: IntentEntry = {
      id: `intent-${Date.now()}`,
      text: intentText.value,
      mood: intentMood.value,
      type: intentType.value,
      theme: intentTheme.value,
      timestamp: new Date().toISOString(),
    };
    intentHistory.value = [intent, ...intentHistory.value].slice(0, 10);
  }

  function loadIntentFromHistory(intent: IntentEntry): void {
    intentText.value = intent.text;
    intentMood.value = intent.mood || '';
    intentType.value = intent.type || '';
    intentTheme.value = intent.theme || '';
  }

  function clearIntentHistory(): void {
    intentHistory.value = [];
  }

  return {
    bodySelection,
    intentText,
    intentGenre,
    intentMood,
    intentType,
    intentTheme,
    intentHistory,
    captureBodySelection,
    saveIntentToHistory,
    loadIntentFromHistory,
    clearIntentHistory,
  };
}