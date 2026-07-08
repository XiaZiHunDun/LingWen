/**
 * useCreatorAgent — 写作导演（预览 A / 确认应用 B2）
 * 计划生成对接 POST /api/creator/agent/plan，失败时降级本地 mock
 */
import { computed, ref, watch } from 'vue';
import { runCreatorAgentPlan, runCreatorAgentPlanStream } from '../api/index.js';
import { AGENT_EXECUTION_MODES, AGENT_LENS_MODES } from '../config/creatorPanelMatrix.js';

const REWRITE_LABELS = {
  concrete: '更具体',
  dramatic: '更戏剧',
  restrained: '更克制',
  humorous: '更幽默',
  lyrical: '更抒情',
};

const DIRECTOR_PATH_DEFS = [
  {
    id: 'faster',
    label: '加快节奏',
    actionLabel: '加快节奏',
    consequence: '信息披露前移，悬念减弱但推进加快',
  },
  {
    id: 'restrained',
    label: '更克制',
    actionLabel: '更克制',
    consequence: '情绪降温、留白增加，适合铺垫后段',
  },
  {
    id: 'conflict',
    label: '升级冲突',
    actionLabel: '升级冲突',
    consequence: '对立加深，后续需安排收束与代价',
  },
];

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   getSelection: () => { text: string, start: number, end: number } | null,
 *   getChapterNum: () => number | null,
 *   getBodyDraft: () => string,
 *   getControls: () => {
 *     styleStrength: number,
 *     selectionLocked: boolean,
 *     allowWorldbuildingFill: boolean,
 *     goalTag: string,
 *   },
 *   applyTextToSelection: (text: string) => void,
 *   createCheckpoint: (label: string) => string,
 *   restoreCheckpoint: (id: string) => void,
 *   onAnnotationFocus?: (paragraph: number) => void,
 * }} deps
 */
export function useCreatorAgent(deps) {
  const {
    uiProfile,
    getSelection,
    getChapterNum,
    getBodyDraft,
    getControls,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint,
    onAnnotationFocus,
  } = deps;

  const executionMode = ref(
    uiProfile.value.agent_execution_mode_default === AGENT_EXECUTION_MODES.apply
      ? AGENT_EXECUTION_MODES.apply
      : AGENT_EXECUTION_MODES.preview,
  );
  const agentExpanded = ref(false);
  const promptInput = ref('');
  const messages = ref([]);
  const generating = ref(false);
  const pendingPlan = ref(null);
  const candidates = ref([]);
  const directorAdvice = ref([]);
  const lastCheckpointId = ref(null);
  const statusLine = ref('');
  const planProvider = ref('local');
  const agentLens = ref(uiProfile.value.agent_lens_default || 'author');

  const agentLensLabel = computed(() => {
    const found = AGENT_LENS_MODES.find((m) => m.id === agentLens.value);
    return found?.label || agentLens.value;
  });
  const annotations = ref([]);

  const streamPreviewText = ref('');
  const streamPreviewLabel = ref('');
  const streamSource = ref(null);
  const streamAdvicePreview = ref([]);

  const hasPendingPlan = computed(() => Boolean(pendingPlan.value));
  const isPreviewMode = computed(() => executionMode.value === AGENT_EXECUTION_MODES.preview);

  const currentScope = computed(() => buildScope());

  const directorPaths = computed(() => {
    const scope = currentScope.value;
    if (scope.type === 'none') return [];
    const controls = getControls();
    const goal = controls.goalTag;
    return DIRECTOR_PATH_DEFS.map((path) => {
      let consequence = path.consequence;
      if (goal === 'suspense' && path.id === 'faster') {
        consequence = '悬疑感可能减弱，建议保留 1 处未解信息';
      }
      if (goal === 'restraint' && path.id === 'conflict') {
        consequence = '与「克制」目标冲突，冲突升级需更精准的台词';
      }
      if (goal === 'pace' && path.id === 'restrained') {
        consequence = '节奏目标下留白增多，当前节拍可能偏慢';
      }
      return { ...path, consequence, scopeLabel: scope.label };
    });
  });

  function pushMessage(role, text) {
    messages.value = [...messages.value.slice(-12), { role, text, at: Date.now() }];
  }

  function buildScope() {
    const sel = getSelection();
    if (sel?.text?.trim()) {
      return {
        type: 'selection',
        label: `选区 · ${sel.text.length} 字`,
        selection: sel,
      };
    }
    const ch = getChapterNum();
    if (ch != null) {
      return {
        type: 'chapter',
        label: `ch${String(ch).padStart(3, '0')} 正文`,
        chapter: ch,
      };
    }
    return { type: 'none', label: '无选区/章节焦点' };
  }

  function scopeToApiPayload(scope) {
    return {
      type: scope.type,
      chapter: scope.chapter ?? getChapterNum(),
      selection_text: scope.selection?.text ?? null,
    };
  }

  function mockCandidates(baseText, actionLabel, controls) {
    const seed = baseText?.trim() || '（待生成内容）';
    const fillNote = controls.allowWorldbuildingFill ? '' : '（不补全世界观）';
    return [
      { id: 'steady', label: '稳健', direction: '更稳健', text: `${seed}\n\n[${actionLabel} · 稳健候选${fillNote}]` },
      { id: 'balanced', label: '平衡', direction: '更平衡', text: `${seed}\n\n[${actionLabel} · 平衡候选${fillNote}]` },
      { id: 'bold', label: '大胆', direction: '更戏剧', text: `${seed}\n\n[${actionLabel} · 大胆候选${fillNote}]` },
    ];
  }

  function mockAdvice(actionLabel, path) {
    return [
      { id: 'a1', text: `可先缩短铺垫句，再进入「${actionLabel}」的核心动作` },
      { id: 'a2', text: path?.consequence || '注意本章与上一章的情绪承接' },
      { id: 'a3', text: '保留一句你满意的原句作为锚点，其余再改' },
    ];
  }

  function mockAnnotations(lens, actionLabel) {
    if (lens === 'editor') {
      return [
        { id: 'e1', level: 'warn', text: `铺垫略长，进入「${actionLabel}」前可删 1 句`, paragraph: 1 },
        { id: 'e2', level: 'info', text: '对话信息量可再集中', paragraph: 2 },
      ];
    }
    if (lens === 'reviewer') {
      return [
        { id: 'r1', level: 'warn', text: '读者可能尚不清楚角色当下目标', paragraph: 1 },
      ];
    }
    return [];
  }

  function applyLocalPlan(action, actionLabel, scope, pathMeta, controls) {
    const base = scope.type === 'selection'
      ? scope.selection.text
      : getBodyDraft();

    annotations.value = mockAnnotations(agentLens.value, actionLabel);

    if (controls.styleStrength === 0) {
      directorAdvice.value = mockAdvice(actionLabel, pathMeta);
      pendingPlan.value = {
        action,
        actionLabel,
        scope,
        executionMode: executionMode.value,
        adviceOnly: true,
      };
      statusLine.value = '导演建议已就绪（只建议模式，不改正文）';
      planProvider.value = 'local';
      return;
    }

    const cands = mockCandidates(base, actionLabel, controls);
    pendingPlan.value = {
      action,
      actionLabel,
      scope,
      executionMode: executionMode.value,
      pathMeta,
    };
    candidates.value = cands;
    statusLine.value = isPreviewMode.value
      ? '候选已就绪（预览模式，不覆盖正文）'
      : '请确认后应用（将创建回滚点）';
    planProvider.value = 'local';
    pushMessage('agent', `准备对${scope.label}执行「${actionLabel}」，已生成 ${cands.length} 个候选。`);
  }

  function applyApiPlanResult(result, action, actionLabel, scope, pathMeta) {
    planProvider.value = result.provider || 'api';
    annotations.value = result.annotations || [];
    if (result.lens) agentLens.value = result.lens;
    if (result.advice_only) {
      directorAdvice.value = result.advice || [];
      pendingPlan.value = {
        action,
        actionLabel,
        scope,
        executionMode: executionMode.value,
        adviceOnly: true,
      };
      statusLine.value = result.status_line || '导演建议已就绪（只建议模式，不改正文）';
      return;
    }

    candidates.value = result.candidates || [];
    pendingPlan.value = {
      action,
      actionLabel,
      scope,
      executionMode: executionMode.value,
      pathMeta,
    };
    statusLine.value = result.status_line || (
      isPreviewMode.value
        ? '候选已就绪（预览模式，不覆盖正文）'
        : '请确认后应用（将创建回滚点）'
    );
    const providerNote = result.provider ? ` · ${result.provider}` : '';
    pushMessage(
      'agent',
      `服务端已生成 ${candidates.value.length} 个候选${providerNote}`,
    );
  }

  function clearPlan() {
    pendingPlan.value = null;
    candidates.value = [];
    directorAdvice.value = [];
    annotations.value = [];
  }

  function resetStreamPreview() {
    streamPreviewText.value = '';
    streamPreviewLabel.value = '';
    streamSource.value = null;
    streamAdvicePreview.value = [];
  }

  function looksLikeJsonStream(text) {
    const t = (text || '').trimStart();
    return t.startsWith('{') || t.startsWith('[') || /^"?(candidates|advice|annotations)"/.test(t);
  }

  const streamDisplayText = computed(() => {
    const raw = streamPreviewText.value;
    if (streamSource.value === 'llm' && looksLikeJsonStream(raw)) {
      const len = raw.length;
      return len < 20 ? '模型输出中…' : `模型输出中…（已接收 ${len} 字）`;
    }
    return raw;
  });

  function handleStreamEvent(evt) {
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

  function buildPlanRequestBody(action, actionLabel, scope, controls) {
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

  async function runPlan(action, actionLabel, pathMeta = null) {
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
      const result = await runCreatorAgentPlanStream(body, handleStreamEvent);
      applyApiPlanResult(result, action, actionLabel, scope, pathMeta);
    } catch {
      try {
        const result = await runCreatorAgentPlan(body);
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

  async function runDirectorPath(pathId) {
    const path = DIRECTOR_PATH_DEFS.find((p) => p.id === pathId);
    if (!path) return;
    await runPlan(`path:${pathId}`, path.actionLabel, path);
  }

  async function submitPrompt() {
    const text = promptInput.value.trim();
    if (!text) return;
    pushMessage('user', text);
    promptInput.value = '';
    await runPlan('prompt', text);
  }

  async function runRewritePreset(presetId) {
    const label = REWRITE_LABELS[presetId] || presetId;
    await runPlan(`rewrite:${presetId}`, label);
  }

  function selectCandidate(candidateId) {
    const cand = candidates.value.find((c) => c.id === candidateId);
    if (!cand) return;
    if (isPreviewMode.value) {
      pendingPlan.value = {
        ...pendingPlan.value,
        selectedCandidateId: candidateId,
        confirmReplace: true,
      };
      statusLine.value = `已选「${cand.label}」候选，请确认替换`;
      return;
    }
    requestApply(candidateId);
  }

  function requestApply(candidateId) {
    const cand = candidates.value.find((c) => c.id === candidateId);
    if (!cand || !pendingPlan.value) return;
    pendingPlan.value = {
      ...pendingPlan.value,
      selectedCandidateId: candidateId,
      awaitingConfirm: true,
    };
    statusLine.value = '确认后将创建回滚点并替换选区';
  }

  function confirmApply() {
    const plan = pendingPlan.value;
    if (!plan || plan.adviceOnly) {
      statusLine.value = '只建议模式：请手动改写或提高风格强度';
      return;
    }
    const controls = getControls();
    if (controls.selectionLocked && plan.scope?.type === 'selection') {
      statusLine.value = '选区已锁定，无法应用';
      return;
    }

    const cand = candidates.value.find((c) => c.id === plan?.selectedCandidateId);
    if (!cand) return;
    if (plan.scope?.type === 'none') return;

    const cpId = createCheckpoint(plan.actionLabel);
    lastCheckpointId.value = cpId;

    if (plan.scope.type === 'selection' || plan.scope.type === 'chapter') {
      applyTextToSelection(cand.text);
    }

    pushMessage('agent', `已应用「${cand.label}」· ${agentLensLabel.value} · 可撤销到版本 ${cpId.slice(0, 8)}`);
    statusLine.value = `已应用（${agentLensLabel.value}）`;
    clearPlan();
  }

  function cancelPlan() {
    clearPlan();
    statusLine.value = '已取消';
  }

  function undoLastApply() {
    if (lastCheckpointId.value) {
      restoreCheckpoint(lastCheckpointId.value);
      statusLine.value = '已恢复到上一确认点';
      pushMessage('agent', '已撤销上次应用');
    }
  }

  function toggleExecutionMode() {
    executionMode.value = isPreviewMode.value
      ? AGENT_EXECUTION_MODES.apply
      : AGENT_EXECUTION_MODES.preview;
    statusLine.value = isPreviewMode.value ? '执行方式：预览（A）' : '执行方式：直接应用（B2，需确认）';
  }

  function dismissAdvice(adviceId) {
    directorAdvice.value = directorAdvice.value.filter((a) => a.id !== adviceId);
  }

  function setAgentLens(lensId) {
    agentLens.value = lensId;
    if (pendingPlan.value && !pendingPlan.value.adviceOnly && annotations.value.length) {
      annotations.value = mockAnnotations(lensId, pendingPlan.value.actionLabel || '改写');
    }
    if (generating.value) {
      statusLine.value = `生成中…（${agentLensLabel.value}）`;
    }
  }

  watch(agentLens, (lens) => {
    if (!pendingPlan.value || pendingPlan.value.adviceOnly) return;
    if (annotations.value.length) {
      annotations.value = mockAnnotations(lens, pendingPlan.value.actionLabel || '改写');
    }
  });

  function focusAnnotation(annotation) {
    if (annotation?.paragraph && onAnnotationFocus) {
      onAnnotationFocus(annotation.paragraph);
    }
  }

  return {
    executionMode,
    agentExpanded,
    promptInput,
    messages,
    generating,
    pendingPlan,
    candidates,
    directorAdvice,
    directorPaths,
    currentScope,
    lastCheckpointId,
    statusLine,
    planProvider,
    agentLens,
    agentLensLabel,
    annotations,
    streamPreviewText,
    streamPreviewLabel,
    streamSource,
    streamDisplayText,
    streamAdvicePreview,
    hasPendingPlan,
    isPreviewMode,
    rewritePresets: REWRITE_LABELS,
    submitPrompt,
    runRewritePreset,
    runDirectorPath,
    runPlan,
    selectCandidate,
    confirmApply,
    cancelPlan,
    undoLastApply,
    toggleExecutionMode,
    dismissAdvice,
    setAgentLens,
    focusAnnotation,
    clearPlan,
    buildScope,
  };
}
