/**
 * useAgentTask — Agent 任务执行（runPlan/director path/prompt/chat/ask）
 *
 * Phase 19 Task 6：从 useCreatorAgent.js 拆出（完整实现）。
 * 负责: runPlan + runDirectorPath + submitPrompt + chat + ask + runRewritePreset +
 *       messages state + generating state + statusLine + planProvider +
 *       streamPreview* + annotations + applyLocalPlan + applyApiPlanResult +
 *       handleStreamEvent + resetStreamPreview。
 *
 * 注: 通过 deps 接收 pendingPlan/candidates/directorAdvice 等共享 ref（由 useAgentTools 拥有）。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { runCreatorAgentPlan, runCreatorAgentPlanStream } from '../../api/index.js';
import { AGENT_EXECUTION_MODES } from '../../config/creatorPanelMatrix.js';

const REWRITE_LABELS_TASK: Record<string, string> = {
  concrete: '更具体',
  dramatic: '更戏剧',
  restrained: '更克制',
  humorous: '更幽默',
  lyrical: '更抒情',
};

const DIRECTOR_PATH_DEFS_TASK = [
  { id: 'faster', label: '加快节奏', actionLabel: '加快节奏', consequence: '信息披露前移，悬念减弱但推进加快' },
  { id: 'restrained', label: '更克制', actionLabel: '更克制', consequence: '情绪降温、留白增加，适合铺垫后段' },
  { id: 'conflict', label: '升级冲突', actionLabel: '升级冲突', consequence: '对立加深，后续需安排收束与代价' },
];

interface AgentScope {
  type: 'selection' | 'chapter' | 'none';
  label: string;
  selection?: { text: string; start: number; end: number };
  chapter?: number;
}

interface AgentControls {
  styleStrength: number;
  selectionLocked: boolean;
  allowWorldbuildingFill: boolean;
  goalTag: string;
}

interface AgentPlan {
  action: string;
  actionLabel: string;
  scope: AgentScope;
  executionMode: string;
  adviceOnly?: boolean;
  pathMeta?: unknown;
  selectedCandidateId?: string;
  confirmReplace?: boolean;
  awaitingConfirm?: boolean;
}

interface AgentMessage {
  role: 'user' | 'assistant' | 'agent';
  text: string;
  at: number;
}

interface AgentCandidate {
  id: string;
  label: string;
  direction?: string;
  text: string;
}

interface AgentAdvice {
  id: string;
  text: string;
}

export interface AgentTaskDeps {
  executionMode: Ref<string>;
  agentLens: Ref<string>;
  agentLensLabel: ComputedRef<string>;
  getSelection: () => { text: string; start: number; end: number } | null;
  getChapterNum: () => number | null;
  getBodyDraft: () => string;
  getControls: () => AgentControls;
  pendingPlan: Ref<AgentPlan | null>;
  candidates: Ref<AgentCandidate[]>;
  directorAdvice: Ref<AgentAdvice[]>;
  annotations: Ref<Array<Record<string, unknown>>>;
}

export interface AgentTaskReturn {
  messages: Ref<AgentMessage[]>;
  generating: Ref<boolean>;
  statusLine: Ref<string>;
  planProvider: Ref<string>;
  streamPreviewText: Ref<string>;
  streamPreviewLabel: Ref<string>;
  streamSource: Ref<string | null>;
  streamAdvicePreview: Ref<string[]>;
  streamDisplayText: ComputedRef<string>;
  currentScope: ComputedRef<AgentScope>;
  pushMessage: (role: AgentMessage['role'], text: string) => void;
  buildScope: () => AgentScope;
  scopeToApiPayload: (scope: AgentScope) => Record<string, unknown>;
  mockCandidates: (baseText: string, actionLabel: string, controls: AgentControls) => AgentCandidate[];
  mockAdvice: (actionLabel: string, pathMeta?: { consequence?: string }) => AgentAdvice[];
  mockAnnotations: (lens: string, actionLabel: string) => Array<Record<string, unknown>>;
  buildPlanRequestBody: (action: string, actionLabel: string, scope: AgentScope, controls: AgentControls) => Record<string, unknown>;
  runPlan: (action: string, actionLabel: string, pathMeta?: unknown) => Promise<void>;
  runDirectorPath: (pathId: string) => Promise<void>;
  submitPrompt: () => Promise<void>;
  chat: (text: string) => Promise<string>;
  ask: (text: string) => Promise<string>;
  runRewritePreset: (presetId: string) => Promise<void>;
  resetStreamPreview: () => void;
  clearPlan: () => void;
  handleStreamEvent: (evt: { type?: string; message?: string; label?: string; text?: string; source?: string }) => void;
}

export function useAgentTask(deps: AgentTaskDeps): AgentTaskReturn {
  const {
    executionMode,
    agentLens,
    agentLensLabel,
    getSelection,
    getChapterNum,
    getBodyDraft,
    getControls,
    pendingPlan,
    candidates,
    directorAdvice,
    annotations,
  } = deps;

  const messages = ref<AgentMessage[]>([]);
  const generating = ref(false);
  const statusLine = ref('');
  const planProvider = ref('local');

  const streamPreviewText = ref('');
  const streamPreviewLabel = ref('');
  const streamSource = ref<string | null>(null);
  const streamAdvicePreview = ref<string[]>([]);

  function pushMessage(role: AgentMessage['role'], text: string): void {
    messages.value = [...messages.value.slice(-12), { role, text, at: Date.now() }];
  }

  function buildScope(): AgentScope {
    const sel = getSelection();
    if (sel?.text?.trim()) {
      return { type: 'selection', label: `选区 · ${sel.text.length} 字`, selection: sel };
    }
    const ch = getChapterNum();
    if (ch != null) {
      return { type: 'chapter', label: `ch${String(ch).padStart(3, '0')} 正文`, chapter: ch };
    }
    return { type: 'none', label: '无选区/章节焦点' };
  }

  const currentScope = computed<AgentScope>(() => buildScope());

  function scopeToApiPayload(scope: AgentScope): Record<string, unknown> {
    return {
      type: scope.type,
      chapter: scope.chapter ?? getChapterNum(),
      selection_text: scope.selection?.text ?? null,
    };
  }

  function mockCandidates(baseText: string, actionLabel: string, controls: AgentControls): AgentCandidate[] {
    const seed = baseText?.trim() || '（待生成内容）';
    const fillNote = controls.allowWorldbuildingFill ? '' : '（不补全世界观）';
    return [
      { id: 'steady', label: '稳健', direction: '更稳健', text: `${seed}\n\n[${actionLabel} · 稳健候选${fillNote}]` },
      { id: 'balanced', label: '平衡', direction: '更平衡', text: `${seed}\n\n[${actionLabel} · 平衡候选${fillNote}]` },
      { id: 'bold', label: '大胆', direction: '更戏剧', text: `${seed}\n\n[${actionLabel} · 大胆候选${fillNote}]` },
    ];
  }

  function mockAdvice(actionLabel: string, path?: { consequence?: string }): AgentAdvice[] {
    return [
      { id: 'a1', text: `可先缩短铺垫句，再进入「${actionLabel}」的核心动作` },
      { id: 'a2', text: path?.consequence || '注意本章与上一章的情绪承接' },
      { id: 'a3', text: '保留一句你满意的原句作为锚点，其余再改' },
    ];
  }

  function mockAnnotations(lens: string, actionLabel: string): Array<Record<string, unknown>> {
    if (lens === 'editor') {
      return [
        { id: 'e1', level: 'warn', text: `铺垫略长，进入「${actionLabel}」前可删 1 句`, paragraph: 1 },
        { id: 'e2', level: 'info', text: '对话信息量可再集中', paragraph: 2 },
      ];
    }
    if (lens === 'reviewer') {
      return [{ id: 'r1', level: 'warn', text: '读者可能尚不清楚角色当下目标', paragraph: 1 }];
    }
    return [];
  }

  function applyLocalPlan(
    action: string,
    actionLabel: string,
    scope: AgentScope,
    pathMeta: unknown,
    controls: AgentControls,
  ): void {
    const base = scope.type === 'selection' ? (scope.selection?.text || '') : getBodyDraft();
    annotations.value = mockAnnotations(agentLens.value, actionLabel);

    if (controls.styleStrength === 0) {
      directorAdvice.value = mockAdvice(actionLabel, pathMeta as { consequence?: string });
      pendingPlan.value = { action, actionLabel, scope, executionMode: executionMode.value, adviceOnly: true };
      statusLine.value = '导演建议已就绪（只建议模式，不改正文）';
      planProvider.value = 'local';
      return;
    }

    const cands = mockCandidates(base, actionLabel, controls);
    pendingPlan.value = { action, actionLabel, scope, executionMode: executionMode.value, pathMeta };
    candidates.value = cands;
    statusLine.value = executionMode.value === AGENT_EXECUTION_MODES.preview
      ? '候选已就绪（预览模式，不覆盖正文）'
      : '请确认后应用（将创建回滚点）';
    planProvider.value = 'local';
    pushMessage('agent', `准备对${scope.label}执行「${actionLabel}」，已生成 ${cands.length} 个候选。`);
  }

  function applyApiPlanResult(
    result: Record<string, unknown>,
    action: string,
    actionLabel: string,
    scope: AgentScope,
    pathMeta: unknown,
  ): void {
    planProvider.value = (result.provider as string) || 'api';
    annotations.value = (result.annotations as Array<Record<string, unknown>>) || [];
    if (result.lens) agentLens.value = result.lens as string;
    if (result.advice_only) {
      directorAdvice.value = (result.advice as AgentAdvice[]) || [];
      pendingPlan.value = { action, actionLabel, scope, executionMode: executionMode.value, adviceOnly: true };
      statusLine.value = (result.status_line as string) || '导演建议已就绪（只建议模式，不改正文）';
      return;
    }

    candidates.value = (result.candidates as AgentCandidate[]) || [];
    pendingPlan.value = { action, actionLabel, scope, executionMode: executionMode.value, pathMeta };
    statusLine.value = (result.status_line as string) || (
      executionMode.value === AGENT_EXECUTION_MODES.preview
        ? '候选已就绪（预览模式，不覆盖正文）'
        : '请确认后应用（将创建回滚点）'
    );
    const providerNote = result.provider ? ` · ${result.provider}` : '';
    pushMessage('agent', `服务端已生成 ${candidates.value.length} 个候选${providerNote}`);
  }

  function clearPlan(): void {
    pendingPlan.value = null;
    candidates.value = [];
    directorAdvice.value = [];
    annotations.value = [];
  }

  function resetStreamPreview(): void {
    streamPreviewText.value = '';
    streamPreviewLabel.value = '';
    streamSource.value = null;
    streamAdvicePreview.value = [];
  }

  function looksLikeJsonStream(text: string): boolean {
    const t = (text || '').trimStart();
    return t.startsWith('{') || t.startsWith('[') || /^"?(candidates|advice|annotations)"/.test(t);
  }

  const streamDisplayText = computed<string>(() => {
    const raw = streamPreviewText.value;
    if (streamSource.value === 'llm' && looksLikeJsonStream(raw)) {
      const len = raw.length;
      return len < 20 ? '模型输出中…' : `模型输出中…（已接收 ${len} 字）`;
    }
    return raw;
  });

  function handleStreamEvent(evt: { type?: string; message?: string; label?: string; text?: string; source?: string }): void {
    if (!evt || typeof evt !== 'object') return;
    if (evt.type === 'status' && evt.message) {
      statusLine.value = evt.message;
      return;
    }
    if (evt.type === 'preview_label' && evt.label) {
      streamPreviewLabel.value = `${evt.label} · ${agentLensLabel.value}`;
      return;
    }
    if (evt.type === 'chunk' && evt.text) {
      if (evt.source) streamSource.value = evt.source;
      streamPreviewText.value += evt.text;
      return;
    }
    if (evt.type === 'advice' && evt.text) {
      streamAdvicePreview.value = [...streamAdvicePreview.value, evt.text];
    }
  }

  function buildPlanRequestBody(
    action: string,
    actionLabel: string,
    scope: AgentScope,
    controls: AgentControls,
  ): Record<string, unknown> {
    return {
      action,
      action_label: actionLabel,
      scope: scopeToApiPayload(scope),
      body_draft: getBodyDraft(),
      style_strength: controls.styleStrength,
      allow_worldbuilding_fill: controls.allowWorldbuildingFill,
      goal_tag: controls.goalTag || null,
      execution_mode: executionMode.value,
      lens: agentLens.value,
      provider_mode: 'auto',
    };
  }

  async function runPlan(action: string, actionLabel: string, pathMeta: unknown = null): Promise<void> {
    const scope = buildScope();
    const controls = getControls();
    if (scope.type === 'none') {
      statusLine.value = '请先选中段落或打开某一章正文';
      return;
    }
    if (controls.selectionLocked && scope.type === 'selection') {
      statusLine.value = '选区已锁定，无法应用改写（可取消锁定）';
      return;
    }

    generating.value = true;
    resetStreamPreview();
    statusLine.value = '生成中…';
    const body = buildPlanRequestBody(action, actionLabel, scope, controls);
    try {
      const result = await runCreatorAgentPlanStream(body, handleStreamEvent) as Record<string, unknown>;
      applyApiPlanResult(result, action, actionLabel, scope, pathMeta);
    } catch {
      try {
        const result = await runCreatorAgentPlan(body) as Record<string, unknown>;
        applyApiPlanResult(result, action, actionLabel, scope, pathMeta);
      } catch {
        applyLocalPlan(action, actionLabel, scope, pathMeta, controls);
        statusLine.value = `${statusLine.value}（已降级本地）`;
      }
    } finally {
      generating.value = false;
      resetStreamPreview();
    }
  }

  async function runDirectorPath(pathId: string): Promise<void> {
    const path = DIRECTOR_PATH_DEFS_TASK.find((p: { id: string }) => p.id === pathId);
    if (!path) return;
    await runPlan(`path:${pathId}`, path.actionLabel, path);
  }

  async function submitPrompt(): Promise<void> {
    // 由主 hook 实现（依赖 promptInput + runPlan）
    throw new Error('submitPrompt: bind in main hook');
  }

  async function chat(text: string): Promise<string> {
    pushMessage('user', text);
    generating.value = true;
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const response = `我收到了你的消息："${text}"。这是一个模拟的聊天响应。在实际应用中，这里会调用后端 API 获取真实的 AI 响应。`;
      pushMessage('assistant', response);
      return response;
    } finally {
      generating.value = false;
    }
  }

  async function ask(text: string): Promise<string> {
    generating.value = true;
    try {
      await new Promise((resolve) => setTimeout(resolve, 800));
      const response = `关于"${text}"，我的建议是：继续保持写作的节奏，多尝试不同的表达方式，让故事更加生动有趣。`;
      return response;
    } finally {
      generating.value = false;
    }
  }

  async function runRewritePreset(presetId: string): Promise<void> {
    const label = REWRITE_LABELS_TASK[presetId] || presetId;
    await runPlan(`rewrite:${presetId}`, label);
  }

  return {
    messages,
    generating,
    statusLine,
    planProvider,
    streamPreviewText,
    streamPreviewLabel,
    streamSource,
    streamAdvicePreview,
    streamDisplayText,
    currentScope,
    pushMessage,
    buildScope,
    scopeToApiPayload,
    mockCandidates,
    mockAdvice,
    mockAnnotations,
    buildPlanRequestBody,
    runPlan,
    runDirectorPath,
    submitPrompt,
    chat,
    ask,
    runRewritePreset,
    resetStreamPreview,
    clearPlan,
    handleStreamEvent,
  };
}