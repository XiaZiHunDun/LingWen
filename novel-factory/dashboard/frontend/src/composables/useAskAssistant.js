/**
 * Ask assistant — L1 聊聊（frontend-ia-v1）.
 * Orchestrates memory query + overview snippets; offline-safe fallbacks.
 */
import { ref } from 'vue';
import {
  fetchCreatorOverview,
  fetchStudioSummary,
  queryCreatorMemory,
} from '../api/index.js';

/** @type {import('vue').Ref<'chat'|'note'>} */
const sharedAskTab = ref('chat');

/** 顶栏 Tab 与 AskPage 共享 */
export function useAskPageTab() {
  return { tab: sharedAskTab };
}

const NEW_USER_SUGGESTIONS = [
  { id: 'new-book', label: '我想新开一本书', prompt: '我想新开一本书，该怎么开始？' },
  { id: 'capabilities', label: '你能帮我做什么？', prompt: '这个写作助手能帮我做什么？' },
  { id: 'progress', label: '这本书进度如何？', prompt: '这本书写到哪了？' },
];

function formatMemoryHits(hits) {
  if (!hits?.length) return '没有在记忆库里找到直接相关的内容。你可以换个说法，或在「书桌」改正文。';
  return hits.slice(0, 4).map((h, i) => `${i + 1}. ${h.title || h.id || '条目'}：${(h.excerpt || h.text || '').slice(0, 120)}`).join('\n');
}

function formatOverviewProgress(overview, summary) {
  const name = overview?.name || summary?.name || '当前项目';
  const written = overview?.chapters_written ?? summary?.chapter_count ?? 0;
  const max = overview?.max_chapter ?? summary?.max_chapter ?? 0;
  const alerts = overview?.alert_count ?? 0;
  let text = `《${name}》已写 ${written} 章`;
  if (max) text += `，规划至第 ${max} 章`;
  text += '。';
  if (alerts > 0) text += `\n有 ${alerts} 条脉络预警，可在书桌 → 脉络查看。`;
  else text += '\n脉络状态正常。';
  return text;
}

function localWelcome(overview, summary) {
  const name = overview?.name || summary?.name;
  if (!name) {
    return '你好，我是你的写作助手。你可以问我：能做什么、怎么开新书、人物设定、写到哪了。';
  }
  return '你好。你可以问进度、查设定、理这章意图。';
}

async function buildAssistantReply(text, ctx) {
  const q = (text || '').trim();

  if (/新开|创建|开始写|怎么开始/.test(q)) {
    return '开新书三步：① 速记页点「收成新书」走入门向导；② 选写法模板；③ 在「书桌」落第一段。';
  }

  if (/能做什么|怎么用|帮助/.test(q)) {
    return '我可以：\n· 查这本书写到哪、有哪些预警\n· 搜人物、设定、伏笔（记忆库）\n· 帮你理「这章要写什么」（意图，不是长文代写）\n\n正文写作在「书桌」上进行。';
  }

  if (/进度|写到哪|多少字|几章/.test(q)) {
    const overview = ctx.overview || await fetchCreatorOverview().catch(() => null);
    const summary = ctx.summary || await fetchStudioSummary().catch(() => null);
    return formatOverviewProgress(overview, summary);
  }

  try {
    const result = await queryCreatorMemory({ query: q, scope: 'all', top_k: 5 });
    const hits = result?.hits || result?.results || [];
    if (hits.length) {
      return `找到这些相关记忆：\n\n${formatMemoryHits(hits)}`;
    }
  } catch {
    /* offline */
  }

  if (/人物|角色|伏笔|设定|时间线/.test(q)) {
    return '暂时没搜到匹配记忆。你可以先在「书桌」上写一段，或在设定栏补充；之后再问我。';
  }

  return `收到：「${q}」\n\n我还在学习这本书的上下文。你可以试试：\n· 问「这本书进度如何」\n· 问某个人物或设定名`;
}

/**
 * @param {{
 *   onGoWrite?: (chapter?: number|null) => void,
 *   onNewProject?: () => void,
 * }} [hooks]
 */
export function useAskAssistant(hooks = {}) {
  const tab = sharedAskTab;
  const messages = ref([]);
  const draft = ref('');
  const noteDraft = ref('');
  const notes = ref([]);
  const loading = ref(false);
  const context = ref({ overview: null, summary: null });

  async function bootstrap() {
    const [overview, summary] = await Promise.all([
      fetchCreatorOverview().catch(() => null),
      fetchStudioSummary().catch(() => null),
    ]);
    context.value = { overview, summary };
    if (!messages.value.length) {
      messages.value = [{ role: 'assistant', text: localWelcome(overview, summary), at: Date.now() }];
    }
  }

  async function sendMessage(text) {
    const content = (text ?? draft.value).trim();
    if (!content || loading.value) return;
    draft.value = '';
    messages.value = [...messages.value, { role: 'user', text: content, at: Date.now() }];
    loading.value = true;
    try {
      const reply = await buildAssistantReply(content, context.value);
      messages.value = [...messages.value, { role: 'assistant', text: reply, at: Date.now() }];
    } finally {
      loading.value = false;
    }
  }

  function saveNote(text) {
    const t = (text ?? noteDraft.value).trim();
    if (!t) return;
    notes.value = [{ id: `n-${Date.now()}`, text: t, at: Date.now() }, ...notes.value].slice(0, 50);
    if (text == null) noteDraft.value = '';
  }

  function copyToNote(text) {
    const t = (text || '').trim();
    if (!t) return;
    saveNote(t);
    tab.value = 'note';
  }

  function goWrite() {
    hooks.onGoWrite?.(context.value.overview?.latest_chapter ?? null);
  }

  function startNewProject() {
    hooks.onNewProject?.();
  }

  return {
    tab,
    messages,
    draft,
    noteDraft,
    notes,
    loading,
    suggestions: NEW_USER_SUGGESTIONS,
    bootstrap,
    sendMessage,
    saveNote,
    copyToNote,
    goWrite,
    startNewProject,
  };
}
