'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

interface Book {
  id: number;
  title: string;
  genre: string | null;
  summary: string | null;
  style: string | null;
  updatedAt: string | null;
}

interface Outline {
  id: number;
  seq: number | null;
  title: string;
  summary: string | null;
}

/** 大纲区渲染用的行：id 为 null 表示本地新增、尚未落库的空白草稿。 */
interface OutlineRow {
  key: string;
  id: number | null;
  seq: number | null;
  title: string;
  summary: string;
}

interface Chapter {
  id: number;
  seq: number | null;
  title: string;
  content: string | null;
  wordCount: number | null;
}

interface BibleItem {
  id: number;
  category: string | null;
  title: string | null;
  content: string | null;
}

interface CheckStats {
  chapterCount: number;
  totalWords: number;
  outlineCoverage: number;
  llmCalls: number;
}

interface CheckIssue {
  level: string;
  message: string;
}

/** 单章 AI 检查的严重级别。 */
type ReviewLevel = 'error' | 'warn';

/** 单章 AI 检查返回的一条问题（与 /api/books/[id]/check 的 CheckIssue 无关）。 */
interface ReviewIssue {
  level: ReviewLevel;
  quote: string;
  suggestion: string;
}

/** 单章 AI 检查结果。 */
interface ReviewResult {
  issues: ReviewIssue[];
  summary: string;
}

type GenerateMode = 'append' | 'replace';

const DEFAULT_TARGET_WORDS = 1200;
const UNTITLED = '未命名';

/** 读取后端返回的 error 字段；响应体不是 JSON 时回退到状态码文案。 */
async function readErrorMessage(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { error?: unknown };
    if (typeof data.error === 'string' && data.error.trim() !== '') return data.error;
  } catch {
    // 响应体不是 JSON，忽略
  }
  return `请求失败（HTTP ${res.status}）`;
}

/** GET 一个 JSON 接口：非 2xx 一律抛错，错误文本取后端 error 字段。 */
async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(await readErrorMessage(res));
  return (await res.json()) as T;
}

function toMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

/** 判断错误是否来自 AbortController.abort()（fetch / 流读取均可能抛）。 */
function isAbortError(err: unknown): boolean {
  if (err instanceof Error) return err.name === 'AbortError';
  if (typeof err === 'object' && err !== null && 'name' in err) {
    const name = (err as { name?: unknown }).name;
    return name === 'AbortError';
  }
  return false;
}

function seqLabel(seq: number | null): string {
  return seq === null ? '-' : String(seq);
}

/** 标题为空时统一落成「未命名」。 */
function normalizeTitle(value: string): string {
  const trimmed = value.trim();
  return trimmed === '' ? UNTITLED : trimmed;
}

/** 服务端大纲列表 → 可编辑行列表。 */
function outlineRowsFromItems(items: Outline[]): OutlineRow[] {
  return items.map((item) => ({
    key: `outline-${item.id}`,
    id: item.id,
    seq: item.seq,
    title: item.title,
    summary: item.summary ?? '',
  }));
}

/** 设定集条目正文截断到 80 字，列表里只做预览。 */
function bibleSnippet(content: string): string {
  const flat = content.replace(/\s+/g, ' ').trim();
  return flat.length > 80 ? `${flat.slice(0, 80)}…` : flat;
}

/** 设定集条目的「分类 · 标题」标题行。 */
function bibleHead(item: BibleItem): string {
  const parts: string[] = [];
  if (item.category !== null && item.category.trim() !== '') parts.push(item.category.trim());
  if (item.title !== null && item.title.trim() !== '') parts.push(item.title.trim());
  return parts.length === 0 ? '未命名设定' : parts.join(' · ');
}

/** 覆盖率是 0~1 的小数，展示成百分比。 */
function formatCoverage(value: number): string {
  return `${Math.round(value * 100)}%`;
}

/** 自动保存状态：idle 空闲 / saving 保存中 / saved 已保存 / error 失败。 */
type AutoSaveState =
  | { status: 'idle' }
  | { status: 'saving' }
  | { status: 'saved'; at: string }
  | { status: 'error'; message: string };

/** 本地时间 HH:mm:ss（补零），用于自动保存提示。 */
function formatClockTime(date: Date): string {
  const pad = (value: number): string => String(value).padStart(2, '0');
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

/** 章节历史版本列表项：后端只回元信息 + 80 字预览，不含全文。 */
interface ChapterRevisionSummary {
  id: string;
  source: string;
  wordCount: number;
  createdAt: string;
  preview: string;
}

/** 章节历史版本详情：含全文，用于只读预览与恢复。 */
interface ChapterRevisionDetail {
  id: string;
  chapterId: number | string;
  content: string | null;
  wordCount: number | null;
  source: string;
  createdAt: string;
}

/** 版本来源 → 中文标签（manual / generate / restore / pre-restore）。 */
const REVISION_SOURCE_LABELS: Record<string, string> = {
  manual: '手动保存',
  generate: 'AI 生成',
  restore: '版本恢复',
  'pre-restore': '恢复前备份',
};

/** 来源不在白名单内时原样回显，避免静默丢信息。 */
function revisionSourceLabel(source: string): string {
  return REVISION_SOURCE_LABELS[source] ?? source;
}

/** 版本时间：库里存 UTC 'YYYY-MM-DD HH:MM:SS'，展示成本地 MM-DD HH:mm。 */
function formatRevisionTime(value: string): string {
  const matched = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/.exec(value.trim());
  if (matched === null) return value;
  const date = new Date(
    Date.UTC(
      Number(matched[1]),
      Number(matched[2]) - 1,
      Number(matched[3]),
      Number(matched[4]),
      Number(matched[5]),
      Number(matched[6]),
    ),
  );
  if (Number.isNaN(date.getTime())) return value;
  const pad = (value2: number): string => String(value2).padStart(2, '0');
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function BookDetailPage() {
  const params = useParams<{ id: string }>();
  const bookId = Number(params.id);

  const [book, setBook] = useState<Book | null>(null);
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [bible, setBible] = useState<BibleItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const noticeTimer = useRef<number | null>(null);
  // 章节保存：已保存基线、已同步章节 id、自动保存计时器、串行保存队列、自动保存文案。
  const savedChapterRef = useRef<{ title: string; content: string }>({ title: '', content: '' });
  const syncedChapterIdRef = useRef<number | null>(null);
  const autoSaveTimer = useRef<number | null>(null);
  const saveQueueRef = useRef<Promise<void>>(Promise.resolve());
  const selectedIdRef = useRef<number | null>(null);
  const [autoSave, setAutoSave] = useState<AutoSaveState>({ status: 'idle' });
  // 底部状态栏：保存状态埋点（与现有自动保存 / 手动保存共用同一入口）+ 选区字数。
  const [saveState, setSaveState] = useState<'saved' | 'unsaved' | 'saving' | 'error'>('saved');
  /** 最近一次章节保存成功的时间（HH:MM:SS），null 表示本次会话尚未保存过。独立于 autoSave，仅用于编辑器顶部只读小字。 */
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
  const [selectionCount, setSelectionCount] = useState(0);
  const editorTextareaRef = useRef<HTMLTextAreaElement | null>(null);
  const saveStateLabel =
    saveState === 'saved'
      ? '已保存'
      : saveState === 'unsaved'
        ? '未保存'
        : saveState === 'saving'
          ? '保存中'
          : '保存失败';
  // 选区字数与 charCount 同一口径：去掉空白后按字符计数。
  const syncSelectionCount = (textarea: HTMLTextAreaElement): void => {
    const start = textarea.selectionStart ?? 0;
    const end = textarea.selectionEnd ?? 0;
    if (end <= start) {
      setSelectionCount(0);
      return;
    }
    setSelectionCount(textarea.value.slice(start, end).replace(/\s/g, '').length);
  };

  // 章节历史版本：面板展开状态、版本列表、当前预览详情、加载/恢复进行中。
  const [showRevisions, setShowRevisions] = useState(false);
  const [revisions, setRevisions] = useState<ChapterRevisionSummary[]>([]);
  const [revisionPreview, setRevisionPreview] = useState<ChapterRevisionDetail | null>(null);
  const [revisionsLoading, setRevisionsLoading] = useState(false);
  const [restoringRevisionId, setRestoringRevisionId] = useState<string | null>(null);

  // 大纲：可编辑行 + 当前展开编辑的行 key 与草稿
  const [outlineRows, setOutlineRows] = useState<OutlineRow[]>([]);
  const [editingOutlineKey, setEditingOutlineKey] = useState<string | null>(null);
  const [draftOutlineTitle, setDraftOutlineTitle] = useState('');
  const [draftOutlineSummary, setDraftOutlineSummary] = useState('');
  const [savingOutlines, setSavingOutlines] = useState(false);
  const [outlineBusyKey, setOutlineBusyKey] = useState<string | null>(null);
  const outlineDraftSeq = useRef(0);

  // 设定集：列表 + 新增表单
  const [bibleCategory, setBibleCategory] = useState('');
  const [bibleTitle, setBibleTitle] = useState('');
  const [bibleContent, setBibleContent] = useState('');
  const [addingBible, setAddingBible] = useState(false);

  // 体检
  const [checkStats, setCheckStats] = useState<CheckStats | null>(null);
  const [checkIssues, setCheckIssues] = useState<CheckIssue[]>([]);
  const [checking, setChecking] = useState(false);

  // AI 生成
  const [instruction, setInstruction] = useState('');
  const [targetWords, setTargetWords] = useState(String(DEFAULT_TARGET_WORDS));
  const [mode, setMode] = useState<GenerateMode>('append');
  const [genRunning, setGenRunning] = useState(false);

  // 一键续写接下来 N 章：章节数输入、运行中标记、当前章节进度、错误、中止句柄。
  const [batchCount, setBatchCount] = useState('1');
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchProgress, setBatchProgress] = useState<{ title: string; chars: number } | null>(null);
  const [batchError, setBatchError] = useState<string | null>(null);
  const batchAbort = useRef<AbortController | null>(null);

  // 章节润色（流式预览 → 应用 → 撤销）
  const [polishMode, setPolishMode] = useState<'polish' | 'condense' | 'expand'>('polish');
  const [polishInstruction, setPolishInstruction] = useState('');
  const [polishRunning, setPolishRunning] = useState(false);
  const [polishOutput, setPolishOutput] = useState('');
  const [polishError, setPolishError] = useState<string | null>(null);
  const [polishApplying, setPolishApplying] = useState(false);
  const [polishApplied, setPolishApplied] = useState(false);
  const polishAbort = useRef<AbortController | null>(null);

  // 单章 AI 检查
  const [reviewing, setReviewing] = useState(false);
  const [reviewIssues, setReviewIssues] = useState<ReviewIssue[]>([]);
  const [reviewSummary, setReviewSummary] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const generateAbort = useRef<AbortController | null>(null);
  // 创作助手：消息列表 + 输入 + 运行状态
  type AssistMessage = { role: 'user' | 'assistant'; content: string };
  const [assistMessages, setAssistMessages] = useState<AssistMessage[]>([]);
  const [assistInput, setAssistInput] = useState('');
  const [assistRunning, setAssistRunning] = useState(false);
  const [assistError, setAssistError] = useState<string | null>(null);

  // 书籍设置（内联面板）：展开状态、编辑态、保存中。
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [bookTitle, setBookTitle] = useState('');
  const [bookGenre, setBookGenre] = useState('');
  const [bookSummary, setBookSummary] = useState('');
  const [bookStyle, setBookStyle] = useState('');
  const [savingSettings, setSavingSettings] = useState(false);
  // 章节排序 / 删除进行中：避免重复点击。
  const [orderBusy, setOrderBusy] = useState(false);

  // 批量操作：勾选的章节 id / 用于建章的大纲 id / 批量请求进行中标记。
  const [selectedChapterIds, setSelectedChapterIds] = useState<Set<number>>(new Set());
  const [selectedOutlineIds, setSelectedOutlineIds] = useState<Set<number>>(new Set());
  const [batchBusy, setBatchBusy] = useState(false);

  const selectedChapter = chapters.find((item) => item.id === selectedId) ?? null;
  const charCount = editContent.replace(/\s/g, '').length;
  const canReview = selectedChapter !== null && editContent.trim() !== '';
  const hasReviewResult = reviewSummary !== null && reviewError === null;
  // 未保存修改：标题或正文与「已保存基线」不一致。
  const isDirty =
    selectedId !== null &&
    (editTitle !== savedChapterRef.current.title || editContent !== savedChapterRef.current.content);
  const autoSaveText =
    autoSave.status === 'saving'
      ? '自动保存中…'
      : autoSave.status === 'saved'
        ? `已自动保存 ${autoSave.at}`
        : null;

  const showNotice = useCallback((text: string) => {
    setNotice(text);
    if (noticeTimer.current !== null) window.clearTimeout(noticeTimer.current);
    noticeTimer.current = window.setTimeout(() => setNotice(null), 3000);
  }, []);

  useEffect(
    () => () => {
      if (noticeTimer.current !== null) window.clearTimeout(noticeTimer.current);
      generateAbort.current?.abort();
      batchAbort.current?.abort();
    },
    [],
  );

  // 首屏：并行拉书籍 / 大纲 / 章节 / 设定集。
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setLoadError(null);
      try {
        const [bookData, outlineData, chapterData, bibleData] = await Promise.all([
          getJson<{ book: Book }>(`/api/books/${bookId}`),
          getJson<{ outlines: Outline[] }>(`/api/books/${bookId}/outline`),
          getJson<{ chapters: Chapter[] }>(`/api/books/${bookId}/chapters`),
          getJson<{ items: BibleItem[] }>(`/api/books/${bookId}/bible`),
        ]);
        if (cancelled) return;
        setBook(bookData.book);
        setOutlines(outlineData.outlines);
        setChapters(chapterData.chapters);
        setBible(bibleData.items);
      } catch (err) {
        if (!cancelled) setLoadError(toMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [bookId, reloadKey]);

  // 从全局搜索跳转过来时（?chapter=<id>）：首屏数据就绪后一次性选中目标章节。
  // 用 ref 标记「已处理」，之后章节数据刷新不会再覆盖用户的手动选择。
  const chapterDeepLinkDone = useRef(false);
  useEffect(() => {
    if (chapterDeepLinkDone.current) return;
    if (loading || chapters.length === 0) return;
    chapterDeepLinkDone.current = true;
    const matched = /[?&]chapter=(\d+)/.exec(window.location.search);
    if (matched === null) return;
    const targetId = Number(matched[1]);
    if (!Number.isFinite(targetId)) return;
    if (chapters.some((item) => item.id === targetId)) setSelectedId(targetId);
  }, [loading, chapters]);

  // 服务端大纲变化时重建可编辑行（本地新增的空白草稿随刷新丢弃）。
  useEffect(() => {
    setOutlineRows(outlineRowsFromItems(outlines));
  }, [outlines]);

  // 切换选中章节时同步编辑态，避免串内容。
  // 同一章节的列表刷新（保存后 refreshChapters）不再覆盖编辑区，避免打断输入/光标跳动。
  useEffect(() => {
    if (selectedChapter === null) {
      syncedChapterIdRef.current = null;
      savedChapterRef.current = { title: '', content: '' };
      setEditTitle('');
      setEditContent('');
      return;
    }
    if (syncedChapterIdRef.current === selectedChapter.id) return;
    syncedChapterIdRef.current = selectedChapter.id;
    savedChapterRef.current = {
      title: selectedChapter.title,
      content: selectedChapter.content ?? '',
    };
    setEditTitle(selectedChapter.title);
    setEditContent(selectedChapter.content ?? '');
  }, [selectedChapter]);

  // 切换章节时清空单章 AI 检查结果（其它 setSelectedId 路径也会覆盖到）。
  useEffect(() => {
    setReviewIssues([]);
    setReviewSummary(null);
    setReviewError(null);
  }, [selectedId]);

  // 切换章节时收起历史版本面板并清空旧章节的版本数据，避免串内容。
  useEffect(() => {
    setShowRevisions(false);
    setRevisions([]);
    setRevisionPreview(null);
    setRestoringRevisionId(null);
  }, [selectedId]);

  const refreshOutlines = useCallback(async () => {
    const data = await getJson<{ outlines: Outline[] }>(`/api/books/${bookId}/outline`);
    setOutlines(data.outlines);
  }, [bookId]);

  const refreshChapters = useCallback(async () => {
    const data = await getJson<{ chapters: Chapter[] }>(`/api/books/${bookId}/chapters`);
    setChapters(data.chapters);
    return data.chapters;
  }, [bookId]);

  const refreshBible = useCallback(async () => {
    const data = await getJson<{ items: BibleItem[] }>(`/api/books/${bookId}/bible`);
    setBible(data.items);
  }, [bookId]);

  // 供异步保存回写时判断章节是否已被切换。
  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);

  /**
   * 统一章节保存入口：保存按钮 / 自动保存 / Cmd(Ctrl)+S 共用。
   * silent 模式只刷新章节列表并更新自动保存文案，不切全屏 loading、不弹全局 toast。
   * 成功后不把服务端返回值回写到编辑器，只更新「已保存基线」，避免打断输入与光标跳动。
   */
  const saveChapter = useCallback(
    async (options?: { silent?: boolean }): Promise<void> => {
      const silent = options?.silent === true;
      const chapterId = selectedId;
      if (chapterId === null) return;
      const title = editTitle;
      const content = editContent;

      const run = async (): Promise<void> => {
        setSaveState('saving');
        if (silent) {
          setAutoSave({ status: 'saving' });
        } else {
          setSaving(true);
          setActionError(null);
        }
        try {
          const res = await fetch(`/api/chapters/${chapterId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content }),
          });
          if (!res.ok) throw new Error(await readErrorMessage(res));
          setSaveState('saved');
          // 手动保存与静默自动保存共用此成功分支，两条路径都要刷新「最后保存」时间。
          setLastSavedAt(formatClockTime(new Date()));
          await refreshChapters();
          if (selectedIdRef.current !== chapterId) return;
          savedChapterRef.current = { title, content };
          if (silent) {
            setAutoSave({ status: 'saved', at: formatClockTime(new Date()) });
          } else {
            showNotice('已保存');
          }
        } catch (err) {
          const message = toMessage(err);
          setSaveState('error');
          if (silent) {
            setAutoSave({ status: 'error', message });
          } else {
            setActionError(message);
          }
        } finally {
          if (!silent) setSaving(false);
        }
      };

      // 串行化保存请求，避免并发 PATCH 乱序覆盖服务端内容。
      saveQueueRef.current = saveQueueRef.current.then(run, run);
      await saveQueueRef.current;
    },
    [editContent, editTitle, refreshChapters, selectedId, showNotice],
  );

  /** 自动保存：编辑停顿 1.5s 后静默保存；仅在选中章节且内容与基线不一致时触发。 */
  useEffect(() => {
    if (selectedId === null) return undefined;
    const baseline = savedChapterRef.current;
    if (editTitle === baseline.title && editContent === baseline.content) return undefined;
    if (autoSaveTimer.current !== null) window.clearTimeout(autoSaveTimer.current);
    autoSaveTimer.current = window.setTimeout(() => {
      autoSaveTimer.current = null;
      void saveChapter({ silent: true });
    }, 1500);
    return () => {
      if (autoSaveTimer.current !== null) {
        window.clearTimeout(autoSaveTimer.current);
        autoSaveTimer.current = null;
      }
    };
  }, [editContent, editTitle, saveChapter, selectedId]);

  /** 切换章节：清掉自动保存 timer 并重置自动保存文案。 */
  useEffect(() => {
    if (autoSaveTimer.current !== null) {
      window.clearTimeout(autoSaveTimer.current);
      autoSaveTimer.current = null;
    }
    setAutoSave({ status: 'idle' });
  }, [selectedId]);

  /** Cmd/Ctrl + S：拦截浏览器保存对话框，改为手动保存。 */
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent): void => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
        event.preventDefault();
        void saveChapter();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [saveChapter]);

  /** 有未保存修改时拦截页面关闭；保存成功后 isDirty 变 false 自动解除。 */
  useEffect(() => {
    if (!isDirty) return undefined;
    const onBeforeUnload = (event: BeforeUnloadEvent): void => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [isDirty]);

  /** 切换章节：有未保存正文时先确认，避免误丢草稿。 */
  const handleSelectChapter = (chapterId: number) => {
    if (chapterId === selectedId) return;
    // 与自动保存共用同一份「已保存基线」，避免自动保存成功后仍被误判为未保存。
    if (isDirty && !window.confirm('有未保存修改，切换将丢失，继续？')) return;
    setSelectedId(chapterId);
  };

  const handleGenerateOutline = async () => {
    setGenerating(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}/outline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ generate: true, chapters: 8 }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      await refreshOutlines();
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  /** 进入某条大纲的编辑态，把当前值拷进草稿。 */
  const handleStartEditOutline = (row: OutlineRow) => {
    setEditingOutlineKey(row.key);
    setDraftOutlineTitle(row.title);
    setDraftOutlineSummary(row.summary);
  };

  /** 取消编辑：丢弃草稿；本地新增的空白草稿行一并移除。 */
  const handleCancelEditOutline = () => {
    const key = editingOutlineKey;
    setEditingOutlineKey(null);
    setDraftOutlineTitle('');
    setDraftOutlineSummary('');
    if (key === null) return;
    setOutlineRows((prev) =>
      prev.filter((row) => !(row.id === null && row.key === key)),
    );
  };

  /** 底部「新建大纲条目」：本地追加一条空白草稿并立刻进入编辑态。 */
  const handleAddOutlineDraft = () => {
    outlineDraftSeq.current += 1;
    const key = `outline-draft-${outlineDraftSeq.current}`;
    setOutlineRows((prev) => [
      ...prev,
      { key, id: null, seq: prev.length + 1, title: '', summary: '' },
    ]);
    setEditingOutlineKey(key);
    setDraftOutlineTitle('');
    setDraftOutlineSummary('');
  };

  /**
   * 保存大纲：把当前草稿并回行列表，按顺序 seq = 1..N 一次性整体覆盖后端大纲。
   * 标题为空时写成「未命名」，成功后刷新并退出编辑态。
   */
  const handleSaveOutlines = async () => {
    const key = editingOutlineKey;
    const merged = outlineRows.map((row) => {
      const isEditing = key !== null && row.key === key;
      return {
        title: normalizeTitle(isEditing ? draftOutlineTitle : row.title),
        summary: (isEditing ? draftOutlineSummary : row.summary).trim(),
      };
    });
    if (merged.length === 0) {
      setEditingOutlineKey(null);
      return;
    }

    setSavingOutlines(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}/outline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          outlines: merged.map((row, index) => ({
            seq: index + 1,
            title: row.title,
            summary: row.summary,
          })),
        }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      await refreshOutlines();
      setEditingOutlineKey(null);
      setDraftOutlineTitle('');
      setDraftOutlineSummary('');
      showNotice('大纲已保存');
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setSavingOutlines(false);
    }
  };

  /** 据此建章：POST /api/books/[id]/chapters，成功后刷新列表并选中新章节。 */
  const handleCreateChapterFromOutline = async (row: OutlineRow) => {
    setOutlineBusyKey(row.key);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}/chapters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: normalizeTitle(row.title),
          summary: row.summary,
          outlineId: row.id,
        }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const data = (await res.json()) as { chapter?: Chapter };
      const list = await refreshChapters();
      const createdId = data.chapter?.id;
      if (typeof createdId === 'number') {
        setSelectedId(createdId);
      } else if (list.length > 0) {
        // 兜底：取刷新后列表中 id 最大者
        setSelectedId(list.reduce((max, item) => (item.id > max ? item.id : max), list[0].id));
      }
      showNotice('已按大纲建章');
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setOutlineBusyKey(null);
    }
  };

  const handleCreateChapter = async () => {
    setCreating(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}/chapters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: '新章节' }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const data = (await res.json()) as { chapter?: Chapter };
      const list = await refreshChapters();
      const createdId = data.chapter?.id;
      if (typeof createdId === 'number') {
        setSelectedId(createdId);
      } else if (list.length > 0) {
        // 兜底：取刷新后列表中 id 最大者
        setSelectedId(list.reduce((max, item) => (item.id > max ? item.id : max), list[0].id));
      }
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setCreating(false);
    }
  };

  // 新增设定集条目：成功后清空表单并刷新列表。
  const handleAddBible = async () => {
    setAddingBible(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}/bible`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: bibleCategory.trim(),
          title: bibleTitle.trim(),
          content: bibleContent,
        }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      setBibleCategory('');
      setBibleTitle('');
      setBibleContent('');
      await refreshBible();
      showNotice('设定已添加');
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setAddingBible(false);
    }
  };

  // 删除设定集条目：DELETE /api/bible/[id] 后刷新列表。
  const handleDeleteBible = async (itemId: number) => {
    setActionError(null);
    try {
      const res = await fetch(`/api/bible/${itemId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      await refreshBible();
      showNotice('设定已删除');
    } catch (err) {
      setActionError(toMessage(err));
    }
  };

  // 书籍设置：展开时用 book 当前值初始化编辑态。
  const openBookSettings = () => {
    setBookTitle(book?.title ?? '');
    setBookGenre(book?.genre ?? '');
    setBookSummary(book?.summary ?? '');
    setBookStyle(book?.style ?? '');
    setSettingsOpen(true);
  };

  // 取消：收起面板并丢弃编辑值。
  const cancelBookSettings = () => {
    setSettingsOpen(false);
    setBookTitle(book?.title ?? '');
    setBookGenre(book?.genre ?? '');
    setBookSummary(book?.summary ?? '');
    setBookStyle(book?.style ?? '');
  };

  // 保存书籍设置：PATCH /api/books/[id]，成功后更新 book 状态、收起面板并提示「已保存」。
  const saveBookSettings = async () => {
    const title = bookTitle.trim();
    if (title === '') {
      setActionError('书名不能为空');
      return;
    }
    const genre = bookGenre.trim();
    const summary = bookSummary;
    const style = bookStyle;
    setSavingSettings(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, genre, summary, style }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const payload: unknown = await res.json().catch(() => null);
      const updated =
        payload !== null && typeof payload === 'object' && 'book' in payload
          ? (payload as { book?: Book }).book
          : undefined;
      setBook((prev) => {
        const base = updated ?? prev;
        if (base === null) return prev;
        return {
          ...base,
          title,
          genre: genre === '' ? null : genre,
          summary: summary.trim() === '' ? null : summary,
          style: style.trim() === '' ? null : style,
        };
      });
      setSettingsOpen(false);
      showNotice('已保存');
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setSavingSettings(false);
    }
  };

  // 章节上移 / 下移：本地交换位置，新顺序 seq 依次设为 1..N，仅对 seq 变化的章节 PATCH。
  const handleMoveChapter = async (chapterId: number, offset: -1 | 1) => {
    if (orderBusy) return;
    const from = chapters.findIndex((item) => item.id === chapterId);
    const to = from + offset;
    if (from < 0 || to < 0 || to >= chapters.length) return;
    const previousSeq = new Map<number, number | null>();
    chapters.forEach((item) => {
      previousSeq.set(item.id, item.seq);
    });
    const next = chapters.slice();
    const moved = next[from];
    next.splice(from, 1);
    next.splice(to, 0, moved);
    const reordered = next.map((item, index) => ({ ...item, seq: index + 1 }));
    const changed = reordered.filter(
      (item) => (previousSeq.get(item.id) ?? null) !== item.seq,
    );
    setOrderBusy(true);
    setActionError(null);
    setChapters(reordered);
    try {
      for (const item of changed) {
        const res = await fetch(`/api/chapters/${item.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ seq: item.seq }),
        });
        if (!res.ok) throw new Error(await readErrorMessage(res));
      }
      await refreshChapters();
      showNotice('章节顺序已更新');
    } catch (err) {
      setActionError(toMessage(err));
      await refreshChapters();
    } finally {
      setOrderBusy(false);
    }
  };

  // 已有章节引用到的 outlineId 集合：这些大纲已建章，批量建章时不可勾选。
  const builtOutlineIdSet = new Set<number>();
  for (const item of chapters) {
    const raw = (item as unknown as { outlineId?: unknown }).outlineId;
    if (typeof raw === 'number' && Number.isFinite(raw)) builtOutlineIdSet.add(raw);
  }
  const allChaptersSelected =
    chapters.length > 0 && chapters.every((item) => selectedChapterIds.has(item.id));

  // 勾选 / 取消勾选单个章节。
  const toggleChapterSelected = (chapterId: number) => {
    setSelectedChapterIds((prev) => {
      const next = new Set(prev);
      if (next.has(chapterId)) next.delete(chapterId);
      else next.add(chapterId);
      return next;
    });
  };

  // 全选 / 取消全选章节。
  const toggleSelectAllChapters = () => {
    setSelectedChapterIds(allChaptersSelected ? new Set<number>() : new Set(chapters.map((item) => item.id)));
  };

  // 勾选 / 取消勾选单条大纲（尚未落库或已建章的大纲不可勾选）。
  const toggleOutlineSelected = (outlineId: number | null) => {
    if (outlineId === null || builtOutlineIdSet.has(outlineId)) return;
    setSelectedOutlineIds((prev) => {
      const next = new Set(prev);
      if (next.has(outlineId)) next.delete(outlineId);
      else next.add(outlineId);
      return next;
    });
  };

  // 批量删除章节：confirm 后 POST /api/books/[id]/chapters/batch（action='delete'）。
  // 成功后清空勾选并刷新章节列表；失败时保留勾选便于重试。
  const handleBatchDeleteChapters = async () => {
    const ids = Array.from(selectedChapterIds);
    if (ids.length === 0) {
      setActionError('请先勾选要删除的章节');
      return;
    }
    if (batchBusy || orderBusy) return;
    if (!window.confirm(`确定删除选中的 ${ids.length} 个章节吗？该操作不可撤销。`)) return;
    setBatchBusy(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}/chapters/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'delete', chapterIds: ids }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const payload = (await res.json().catch(() => ({}))) as {
        deleted?: number;
        skipped?: number;
      };
      const deleted = typeof payload.deleted === 'number' ? payload.deleted : 0;
      const skipped = typeof payload.skipped === 'number' ? payload.skipped : 0;
      // 当前编辑中的章节被删掉时清空编辑器（与单章删除口径一致）。
      const currentId = selectedIdRef.current ?? selectedId;
      if (currentId !== null && ids.includes(currentId)) {
        setSelectedId(null);
        setEditTitle('');
        setEditContent('');
        savedChapterRef.current = { title: '', content: '' };
        syncedChapterIdRef.current = null;
      }
      setSelectedChapterIds(new Set());
      await refreshChapters();
      showNotice(skipped > 0 ? `已删除 ${deleted} 个章节，跳过 ${skipped} 个` : `已删除 ${deleted} 个章节`);
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setBatchBusy(false);
    }
  };

  // 批量建章：POST /api/books/[id]/chapters/batch（action='create-from-outline'）。
  // 成功后刷新章节列表与大纲列表（大纲的「已建章」状态依赖章节数据）。
  const handleBatchCreateFromOutline = async () => {
    const ids = Array.from(selectedOutlineIds);
    if (ids.length === 0) {
      setActionError('请先勾选要建章的大纲');
      return;
    }
    if (batchBusy) return;
    setBatchBusy(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/books/${bookId}/chapters/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'create-from-outline', outlineIds: ids }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const payload = (await res.json().catch(() => ({}))) as {
        created?: number;
        skipped?: number;
      };
      const created = typeof payload.created === 'number' ? payload.created : 0;
      const skipped = typeof payload.skipped === 'number' ? payload.skipped : 0;
      setSelectedOutlineIds(new Set());
      await refreshChapters();
      setReloadKey((key) => key + 1);
      showNotice(skipped > 0 ? `已创建 ${created} 个章节，跳过 ${skipped} 个` : `已创建 ${created} 个章节`);
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setBatchBusy(false);
    }
  };

  // 章节删除：confirm 后 DELETE /api/chapters/[id]；删的是当前选中章节则清空编辑器。
  const handleDeleteChapter = async (chapterId: number, chapterTitle: string) => {
    if (orderBusy) return;
    const label = chapterTitle === '' ? UNTITLED : chapterTitle;
    if (!window.confirm(`确定删除章节「${label}」吗？`)) return;
    setOrderBusy(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/chapters/${chapterId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      if (selectedIdRef.current === chapterId || selectedId === chapterId) {
        setSelectedId(null);
        setEditTitle('');
        setEditContent('');
        savedChapterRef.current = { title: '', content: '' };
        syncedChapterIdRef.current = null;
      }
      await refreshChapters();
      showNotice('章节已删除');
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setOrderBusy(false);
    }
  };

  // 体检：GET /api/books/[id]/check，返回 { stats, issues }。
  const handleCheck = async () => {
    setChecking(true);
    setActionError(null);
    try {
      const data = await getJson<{ stats: CheckStats; issues: CheckIssue[] }>(
        `/api/books/${bookId}/check`,
      );
      setCheckStats(data.stats);
      setCheckIssues(data.issues);
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setChecking(false);
    }
  };

  // 单章 AI 检查：POST /api/chapters/[id]/review，返回 { issues, summary }。
  const handleReview = async () => {
    if (selectedChapter === null) return;
    const chapterId = selectedChapter.id;
    setReviewing(true);
    setReviewError(null);
    try {
      const res = await fetch(`/api/chapters/${chapterId}/review`, { method: 'POST' });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const data = (await res.json()) as ReviewResult;
      setReviewIssues(Array.isArray(data.issues) ? data.issues : []);
      setReviewSummary(typeof data.summary === 'string' ? data.summary : null);
    } catch (err) {
      setReviewIssues([]);
      setReviewSummary(null);
      setReviewError(toMessage(err));
    } finally {
      setReviewing(false);
    }
  };

  /** 停止正在进行的 AI 生成（已流入编辑器的内容保留）。 */
  const handleStopGenerate = () => {
    generateAbort.current?.abort();
  };

  // 一键续写的 NDJSON 事件（与 generate-batch 路由输出一一对应）。
  type BatchEvent =
    | { type: 'start'; chapterId: number; title: string }
    | { type: 'delta'; chapterId: number; text: string }
    | { type: 'chapter-done'; chapterId: number; wordCount: number }
    | { type: 'done'; created: number; reason?: string }
    | { type: 'error'; message: string };

  /** 取消一键续写：中止流读取，已生成并落库的章节保留。 */
  const handleCancelBatch = () => {
    batchAbort.current?.abort();
  };

  // 一键续写接下来 N 章：POST /api/books/[id]/chapters/generate-batch，按 NDJSON 行解析事件。
  const handleGenerateBatch = async () => {
    if (batchRunning) return;
    const parsedCount = Number(batchCount);
    const count =
      Number.isFinite(parsedCount) && parsedCount > 0
        ? Math.min(5, Math.max(1, Math.round(parsedCount)))
        : 1;

    const controller = new AbortController();
    batchAbort.current = controller;
    setBatchRunning(true);
    setBatchError(null);
    setBatchProgress(null);

    let buffer = '';
    let createdTotal = 0;
    // abort 后 reader.read() 往往以 { done: true } 正常结束而不抛错，
    // 因此额外记录“取消已提示”标记，保证取消提示只出现一次。
    let cancelNotified = false;

    try {
      const res = await fetch(`/api/books/${bookId}/chapters/generate-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count }),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));

      const reader = res.body?.getReader();
      if (reader !== undefined) {
        const decoder = new TextDecoder();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value === undefined) continue;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n');
          buffer = parts.pop() ?? '';
          for (const part of parts) {
            const line = part.trim();
            if (line === '') continue;
            let event: BatchEvent;
            try {
              event = JSON.parse(line) as BatchEvent;
            } catch {
              continue;
            }
            if (event.type === 'start') {
              setBatchProgress({ title: event.title, chars: 0 });
            } else if (event.type === 'delta') {
              const chars = event.text.replace(/\s/g, '').length;
              setBatchProgress((prev) =>
                prev === null ? prev : { ...prev, chars: prev.chars + chars },
              );
            } else if (event.type === 'chapter-done') {
              createdTotal += 1;
              setBatchProgress((prev) =>
                prev === null ? prev : { ...prev, chars: event.wordCount },
              );
            } else if (event.type === 'error') {
              // 用户已主动取消时不要再写入错误态，统一由取消提示兜底。
              if (!controller.signal.aborted) setBatchError(event.message);
            } else if (event.type === 'done') {
              createdTotal = event.created;
              if (event.created === 0 && event.reason !== undefined) {
                showNotice(event.reason);
              }
            }
          }
        }
      }

      if (controller.signal.aborted) {
        // 用户主动取消：abort 后读取循环通常会以 { done: true } 正常结束（不抛错），
        // 所以必须在循环结束后显式判断取消状态，否则取消提示永远不会出现。
        // 用 cancelNotified 去重，保证同一轮取消只弹一次提示。
        if (!cancelNotified) {
          cancelNotified = true;
          await refreshChapters();
          showNotice('已取消续写（已生成的章节已保存）');
        }
        return;
      }

      await refreshChapters();
      if (createdTotal > 0) showNotice(`一键续写完成，共 ${createdTotal} 章`);
    } catch (err) {
      if (controller.signal.aborted || isAbortError(err)) {
        // 兜底：取消时 reader.read()/fetch 可能抛 TypeError: Failed to fetch（并非 AbortError），
        // 因此以 signal.aborted 作为主判据；cancelNotified 保证同一轮取消只提示一次。
        if (!cancelNotified) {
          cancelNotified = true;
          // 用户主动取消：已生成的章节已在服务端落库，刷新列表即可看到。
          await refreshChapters();
          showNotice('已取消续写（已生成的章节已保存）');
        }
      } else {
        setBatchError(toMessage(err));
      }
    } finally {
      if (batchAbort.current === controller) batchAbort.current = null;
      setBatchRunning(false);
      setBatchProgress(null);
    }
  };

  // AI 生成正文：流式读取，边收边写进编辑区；结束后回读章节同步字数与列表。
  const handleGenerateChapter = async () => {
    // 一键续写进行中时禁止单章生成，避免并发写同一本书。
    if (selectedChapter === null || batchRunning) return;
    const chapterId = selectedChapter.id;
    const parsedWords = Number(targetWords);
    const body = {
      instruction: instruction.trim(),
      targetWords:
        Number.isFinite(parsedWords) && parsedWords > 0
          ? Math.round(parsedWords)
          : DEFAULT_TARGET_WORDS,
      mode,
    };

    const controller = new AbortController();
    generateAbort.current = controller;

    setGenRunning(true);
    setActionError(null);
    if (mode === 'replace') setEditContent('');

    try {
      const res = await fetch(`/api/chapters/${chapterId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));

      const reader = res.body?.getReader();
      if (reader !== undefined) {
        const decoder = new TextDecoder();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value === undefined) continue;
          const chunk = decoder.decode(value);
          if (chunk === '') continue;
          setEditContent((prev) => prev + chunk);
        }
      }

      const detail = await getJson<{ chapter: Chapter }>(`/api/chapters/${chapterId}`);
      await refreshChapters();
      savedChapterRef.current = {
        title: detail.chapter.title,
        content: detail.chapter.content ?? '',
      };
      setEditTitle(detail.chapter.title);
      setEditContent(detail.chapter.content ?? '');
      showNotice(`生成完成，字数 ${detail.chapter.wordCount ?? 0}`);
    } catch (err) {
      if (isAbortError(err)) {
        // 用户主动停止：保留已流入编辑器的增量内容，不回读、不刷新。
        showNotice('已停止生成（已收到的内容保留在编辑器，记得保存）');
      } else {
        setActionError(toMessage(err));
      }
    } finally {
      if (generateAbort.current === controller) generateAbort.current = null;
      setGenRunning(false);
    }
  };

  /** 拉取当前章节的历史版本列表：只在有选中章节时才发请求。 */  /** 取消润色：中止 fetch 并清空预览状态（不动正文）。 */
  const handleCancelPolish = () => {
    polishAbort.current?.abort();
  };

  // 章节润色：POST /api/chapters/[id]/polish，流式逐块追加到预览面板；不落库。
  const handleStartPolish = async () => {
    if (selectedChapter === null || polishRunning) return;
    const chapterId = selectedChapter.id;
    const controller = new AbortController();
    polishAbort.current = controller;
    setPolishRunning(true);
    setPolishError(null);
    setPolishOutput('');
    setPolishApplied(false);

    try {
      const res = await fetch(`/api/chapters/${chapterId}/polish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: polishMode, instruction: polishInstruction.trim() }),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));

      const reader = res.body?.getReader();
      if (reader !== undefined) {
        const decoder = new TextDecoder();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value === undefined) continue;
          const chunk = decoder.decode(value);
          if (chunk === '') continue;
          setPolishOutput((prev) => prev + chunk);
        }
      }
    } catch (err) {
      if (isAbortError(err)) {
        setPolishOutput('');
        showNotice('已取消润色');
      } else {
        setPolishError(toMessage(err));
      }
    } finally {
      if (polishAbort.current === controller) polishAbort.current = null;
      setPolishRunning(false);
    }
  };

  // 应用润色结果：PATCH /api/chapters/[id]（服务端自动快照旧正文），成功后显示「撤销」。
  const handleApplyPolish = async () => {
    const chapterId = selectedId;
    if (chapterId === null || polishRunning || polishApplying) return;
    const nextContent = polishOutput;
    if (nextContent.trim() === '') return;
    setPolishApplying(true);
    setPolishError(null);
    try {
      const res = await fetch(`/api/chapters/${chapterId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: nextContent }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const data = (await res.json()) as { chapter: Chapter };
      if (selectedIdRef.current !== chapterId) return;
      const savedContent = data.chapter.content ?? nextContent;
      setEditContent(savedContent);
      savedChapterRef.current = { title: data.chapter.title, content: savedContent };
      setAutoSave({ status: 'saved', at: formatClockTime(new Date()) });
      setPolishOutput(savedContent);
      setPolishApplied(true);
      showNotice(`润色结果已应用，字数 ${data.chapter.wordCount ?? savedContent.length}`);
      await loadRevisions();
      await refreshChapters();
    } catch (err) {
      setPolishError(toMessage(err));
    } finally {
      setPolishApplying(false);
    }
  };

  // 撤销润色：恢复当前章节 revisions 最新一条（复用现有 handleRestoreRevision）。
  const handleUndoPolish = async () => {
    const chapterId = selectedId;
    if (chapterId === null || polishApplying) return;
    setPolishApplying(true);
    setPolishError(null);
    try {
      const data = await getJson<{ revisions: ChapterRevisionSummary[] }>(
        `/api/chapters/${chapterId}/revisions`,
      );
      if (selectedIdRef.current !== chapterId) return;
      const latest = data.revisions[0];
      if (latest === undefined) {
        setPolishError('没有可撤销的历史版本');
        return;
      }
      await handleRestoreRevision(latest);
      setPolishApplied(false);
      setPolishOutput('');
    } catch (err) {
      setPolishError(toMessage(err));
    } finally {
      setPolishApplying(false);
    }
  };


  const loadRevisions = useCallback(async () => {
    if (selectedId === null) {
      setRevisions([]);
      return;
    }
    const chapterId = selectedId;
    setRevisionsLoading(true);
    try {
      const data = await getJson<{ revisions: ChapterRevisionSummary[] }>(
        `/api/chapters/${chapterId}/revisions`,
      );
      if (selectedIdRef.current !== chapterId) return;
      setRevisions(data.revisions);
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setRevisionsLoading(false);
    }
  }, [selectedId]);

  /** 点开某条历史版本：GET 详情拿全文，放进只读预览。 */
  const handleOpenRevision = async (revision: ChapterRevisionSummary) => {
    const chapterId = selectedId;
    if (chapterId === null) return;
    setActionError(null);
    try {
      const data = await getJson<{ revision: ChapterRevisionDetail }>(
        `/api/chapters/${chapterId}/revisions/${revision.id}`,
      );
      if (selectedIdRef.current !== chapterId) return;
      setRevisionPreview(data.revision);
    } catch (err) {
      setActionError(toMessage(err));
    }
  };

  /**
   * 恢复历史版本：window.confirm 二次确认 → POST .../restore
   * → 用返回的 chapter.content/title 回填编辑器，并同步「已保存基线」（与 saveChapter 同一机制，
   *   因此不会触发自动保存，也不会被未保存拦截误伤）→ 清空预览、刷新版本列表与章节列表。
   */
  const handleRestoreRevision = async (revision: { id: string; createdAt: string }) => {
    const chapterId = selectedId;
    if (chapterId === null) return;
    const confirmed = window.confirm(
      `确定恢复到 ${formatRevisionTime(revision.createdAt)} 的版本？当前正文会先备份为历史版本。`,
    );
    if (!confirmed) return;
    setRestoringRevisionId(revision.id);
    setActionError(null);
    try {
      const res = await fetch(`/api/chapters/${chapterId}/revisions/${revision.id}/restore`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const data = (await res.json()) as { chapter: Chapter };
      if (selectedIdRef.current !== chapterId) return;
      const nextTitle = data.chapter.title;
      const nextContent = data.chapter.content ?? '';
      setEditTitle(nextTitle);
      setEditContent(nextContent);
      savedChapterRef.current = { title: nextTitle, content: nextContent };
      setAutoSave({ status: 'saved', at: formatClockTime(new Date()) });
      setRevisionPreview(null);
      showNotice('已恢复历史版本');
      await loadRevisions();
      await refreshChapters();
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setRestoringRevisionId(null);
    }
  };

  // 创作助手：POST /api/books/[id]/assist，流式 text/plain 累加到末尾的助手消息。
  const handleAssistSend = async () => {
    const question = assistInput.trim();
    if (question === '' || assistRunning) return;
    setAssistInput('');
    setAssistError(null);
    setAssistRunning(true);
    setAssistMessages((prev) =>
      prev.concat([
        { role: 'user', content: question },
        { role: 'assistant', content: '' },
      ]),
    );
    // 按索引更新末尾的助手气泡：函数式 setState，避免闭包拿到旧的 messages。
    const appendToLastAssistant = (chunk: string) => {
      setAssistMessages((prev) => {
        const targetIndex = prev.length - 1;
        const target = prev[targetIndex];
        if (target === undefined || target.role !== 'assistant') return prev;
        return prev.map((message, index): AssistMessage =>
          index === targetIndex ? { role: 'assistant', content: message.content + chunk } : message,
        );
      });
    };
    try {
      const res = await fetch(`/api/books/${bookId}/assist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, chapterId: selectedChapter?.id ?? null }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      const reader = res.body?.getReader();
      if (reader !== undefined) {
        const decoder = new TextDecoder();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value === undefined) continue;
          const chunk = decoder.decode(value, { stream: true });
          if (chunk === '') continue;
          appendToLastAssistant(chunk);
        }
      }
    } catch (err) {
      setAssistError(toMessage(err));
      // 失败时移除末尾仍未产出内容的占位气泡
      setAssistMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last !== undefined && last.role === 'assistant' && last.content === '') {
          return prev.slice(0, -1);
        }
        return prev;
      });
    } finally {
      setAssistRunning(false);
    }
  };

  // —— 窄屏工作台：面板切换（仅 ≤900px 生效，桌面端三栏始终全显示） ——
  type PanelKey = 'outline' | 'editor' | 'bible';
  interface EditorPrefs {
    fontSize: 14 | 16 | 18;
    lineHeight: 1.6 | 1.8 | 2;
    focusMode: boolean;
  }

  const EDITOR_PREFS_KEY = 'lingwen.editor.prefs';
  const DEFAULT_EDITOR_PREFS: EditorPrefs = { fontSize: 16, lineHeight: 1.8, focusMode: false };
  const FONT_SIZE_OPTIONS: Array<EditorPrefs['fontSize']> = [14, 16, 18];
  const LINE_HEIGHT_OPTIONS: Array<EditorPrefs['lineHeight']> = [1.6, 1.8, 2];
  const PANEL_TABS: Array<{ key: PanelKey; label: string }> = [
    { key: 'outline', label: '大纲' },
    { key: 'editor', label: '编辑' },
    { key: 'bible', label: '设定' },
  ];

  const [activePanel, setActivePanel] = useState<PanelKey>('editor');
  const [editorPrefs, setEditorPrefs] = useState<EditorPrefs>(DEFAULT_EDITOR_PREFS);

  // 在 useEffect 中读取 localStorage：首屏渲染默认排版，避免 SSR 与客户端水合不一致。
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(EDITOR_PREFS_KEY);
      if (raw === null) return;
      const parsed: unknown = JSON.parse(raw);
      if (parsed === null || typeof parsed !== 'object') return;
      const source = parsed as Record<string, unknown>;
      const fontSize = source.fontSize;
      const lineHeight = source.lineHeight;
      const focusMode = source.focusMode;
      setEditorPrefs({
        fontSize:
          fontSize === 14 || fontSize === 16 || fontSize === 18
            ? fontSize
            : DEFAULT_EDITOR_PREFS.fontSize,
        lineHeight:
          lineHeight === 1.6 || lineHeight === 1.8 || lineHeight === 2
            ? lineHeight
            : DEFAULT_EDITOR_PREFS.lineHeight,
        focusMode: typeof focusMode === 'boolean' ? focusMode : DEFAULT_EDITOR_PREFS.focusMode,
      });
    } catch {
      // 读取失败（隐私模式 / 脏数据）时退回默认排版，不影响编辑。
    }
  }, []);

  // 更新排版偏好并同步写入 localStorage（key 固定为 lingwen.editor.prefs）。
  const updateEditorPrefs = useCallback((patch: Partial<EditorPrefs>): void => {
    setEditorPrefs((prev) => {
      const next: EditorPrefs = { ...prev, ...patch };
      try {
        window.localStorage.setItem(EDITOR_PREFS_KEY, JSON.stringify(next));
      } catch {
        // 忽略写入失败。
      }
      return next;
    });
  }, []);

  // 面板显隐类：panel-hidden 只在 @media (max-width:900px) 中生效，桌面端三栏照常全显示。
  function panelClassName(key: PanelKey): string {
    return activePanel === key ? 'panel-visible' : 'panel-hidden';
  }

  if (loadError !== null) {
    return (
      <div className="workspace">
        <div className="toolbar">
          <Link href="/">我的书架</Link>
        </div>
        <div className="panel">
          <div className="issue-error">{loadError}</div>
          <div className="toolbar" style={{ marginTop: '0.75rem', justifyContent: 'flex-start' }}>
            <button
              type="button"
              className="btn"
              onClick={() => setReloadKey((key) => key + 1)}
            >
              重试
            </button>
            <Link className="btn btn-ghost" href="/">
              返回书架
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="workspace">
        <div className="panel">
          <p className="muted">加载中…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="workspace">
      {notice !== null ? <div className="notice">{notice}</div> : null}
      <div className="toolbar">
        <div className="stack" style={{ gap: '0.35rem' }}>
          <Link href="/">我的书架</Link>
          <h1 className="page-title">{book === null ? '书籍' : book.title}</h1>
        </div>
        <div className="toolbar-actions">
          <button
            type="button"
            className="btn"
            onClick={() => {
              void handleCheck();
            }}
            disabled={checking}
          >
            {checking ? '检查中…' : '开始检查'}
          </button>
          <a
            className="btn btn-ghost"
            href={`/api/books/${bookId}/export?format=md`}
            target="_blank"
            rel="noreferrer"
          >
            导出 MD
          </a>
          <a
            className="btn btn-ghost"
            href={`/api/books/${bookId}/export?format=txt`}
            target="_blank"
            rel="noreferrer"
          >
            导出 TXT
          </a>
          <a className="btn btn-ghost" href={`/api/books/${bookId}/export/json`} download>
            导出 JSON
          </a>
          <button
            type="button"
            className="btn btn-ghost"
            aria-expanded={settingsOpen}
            onClick={() => {
              if (settingsOpen) {
                cancelBookSettings();
                return;
              }
              openBookSettings();
            }}
          >
            书籍设置
          </button>
          <span className="badge">{book?.genre ?? '未分类'}</span>
        </div>
      </div>

      {actionError !== null ? <div className="issue-error">{actionError}</div> : null}

      {settingsOpen ? (
        <div className="panel stack">
          <h2>书籍设置</h2>
          <div className="field">
            <label htmlFor="book-title">书名</label>
            <input
              id="book-title"
              className="input"
              value={bookTitle}
              onChange={(event) => setBookTitle(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="book-genre">题材</label>
            <input
              id="book-genre"
              className="input"
              value={bookGenre}
              onChange={(event) => setBookGenre(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="book-summary">简介</label>
            <textarea
              id="book-summary"
              className="textarea"
              rows={4}
              value={bookSummary}
              onChange={(event) => setBookSummary(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="book-style">风格</label>
            <textarea
              id="book-style"
              className="textarea"
              rows={3}
              value={bookStyle}
              onChange={(event) => setBookStyle(event.target.value)}
            />
          </div>
          <div className="toolbar">
            <button
              type="button"
              className="btn"
              onClick={() => {
                void saveBookSettings();
              }}
              disabled={savingSettings}
            >
              {savingSettings ? '保存中…' : '保存'}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={cancelBookSettings}
              disabled={savingSettings}
            >
              取消
            </button>
          </div>
        </div>
      ) : null}

      <div className="panel-switch" role="tablist" aria-label="工作台面板切换">
        {PANEL_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={activePanel === tab.key}
            className={activePanel === tab.key ? 'seg-btn active' : 'seg-btn'}
            onClick={() => setActivePanel(tab.key)}
          >
            {tab.label}
          </button>
        ))}
        {editorPrefs.focusMode ? (
          <button
            type="button"
            className="seg-btn active"
            onClick={() => updateEditorPrefs({ focusMode: false })}
          >
            退出专注
          </button>
        ) : null}
      </div>

      <div className={editorPrefs.focusMode ? 'workspace-grid focus-mode' : 'workspace-grid'}>
        <div
          className={`panel stack workspace-column ${panelClassName('outline')}${
            editorPrefs.focusMode ? ' panel-focus-hidden' : ''
          }`}
        >
          <h2>大纲</h2>
          <div className="outline-item stack">
            <div className="outline-row">
              <div className="outline-main">一键续写接下来</div>
              <div className="outline-actions">
                <input
                  type="number"
                  className="input"
                  style={{ maxWidth: '80px' }}
                  min={1}
                  max={5}
                  step={1}
                  aria-label="一键续写的章节数（1-5）"
                  value={batchCount}
                  disabled={batchRunning}
                  onChange={(event) => setBatchCount(event.target.value)}
                />
                <span className="muted">章</span>
                {batchRunning ? (
                  <button type="button" className="btn btn-ghost" onClick={handleCancelBatch}>
                    取消
                  </button>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      void handleGenerateBatch();
                    }}
                  >
                    开始续写
                  </button>
                )}
              </div>
            </div>
            {batchRunning ? (
              <p className="muted">
                {batchProgress === null || batchProgress.title === ''
                  ? '续写中…'
                  : `正在续写：${batchProgress.title}（已生成约 ${batchProgress.chars} 字）`}
              </p>
            ) : null}
            {batchError !== null ? <p className="muted">续写出错：{batchError}</p> : null}
          </div>
          {outlineRows.length === 0 ? (
            <p className="empty">还没有大纲</p>
          ) : (
            <div className="stack">
              {outlineRows.map((row) => (
                <div className="outline-item" key={row.key}>
                  <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
                    <input
                      type="checkbox"
                      aria-label={`选择大纲 ${row.title === '' ? UNTITLED : row.title}`}
                      title={
                        row.id === null
                          ? '未落库的大纲不能批量建章'
                          : builtOutlineIdSet.has(row.id)
                            ? '该大纲已建章'
                            : '勾选后可批量建章'
                      }
                      checked={row.id !== null && selectedOutlineIds.has(row.id)}
                      disabled={row.id === null || builtOutlineIdSet.has(row.id) || batchBusy}
                      onChange={() => toggleOutlineSelected(row.id)}
                    />
                    <span className="muted">
                      {row.id === null
                        ? '未保存'
                        : builtOutlineIdSet.has(row.id)
                          ? '已建章'
                          : '选择'}
                    </span>
                  </div>
                  <div className="outline-row">
                    <div className="outline-main">
                      {seqLabel(row.seq)}. {row.title === '' ? UNTITLED : row.title}
                    </div>
                    <div className="outline-actions">
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => handleStartEditOutline(row)}
                        disabled={savingOutlines || outlineBusyKey !== null}
                      >
                        编辑
                      </button>
                      <button
                        type="button"
                        className="btn"
                        onClick={() => {
                          void handleCreateChapterFromOutline(row);
                        }}
                        disabled={outlineBusyKey !== null || savingOutlines}
                      >
                        {outlineBusyKey === row.key ? '建章中…' : '据此建章'}
                      </button>
                    </div>
                  </div>
                  {row.summary !== '' ? <p className="muted">{row.summary}</p> : null}
                  {editingOutlineKey === row.key ? (
                    <div className="outline-editor stack">
                      <div className="field">
                        <label htmlFor={`outline-title-${row.key}`}>标题</label>
                        <input
                          id={`outline-title-${row.key}`}
                          className="input"
                          value={draftOutlineTitle}
                          placeholder={UNTITLED}
                          onChange={(event) => setDraftOutlineTitle(event.target.value)}
                        />
                      </div>
                      <div className="field">
                        <label htmlFor={`outline-summary-${row.key}`}>摘要</label>
                        <textarea
                          id={`outline-summary-${row.key}`}
                          className="textarea"
                          rows={3}
                          value={draftOutlineSummary}
                          onChange={(event) => setDraftOutlineSummary(event.target.value)}
                        />
                      </div>
                      <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => {
                            void handleSaveOutlines();
                          }}
                          disabled={savingOutlines}
                        >
                          {savingOutlines ? '保存中…' : '保存'}
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={handleCancelEditOutline}
                          disabled={savingOutlines}
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
          <button
            type="button"
            className="btn btn-ghost"
            onClick={handleAddOutlineDraft}
            disabled={savingOutlines}
          >
            新建大纲条目
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              void handleGenerateOutline();
            }}
            disabled={generating}
          >
            {generating ? '生成中…' : 'AI 生成大纲'}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => {
              void handleBatchCreateFromOutline();
            }}
            disabled={selectedOutlineIds.size === 0 || batchBusy || batchRunning}
          >
            {batchBusy ? '处理中…' : `批量建章（已选 ${selectedOutlineIds.size}）`}
          </button>

          <h2>章节</h2>
          <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={toggleSelectAllChapters}
              disabled={chapters.length === 0 || batchBusy}
            >
              {allChaptersSelected
                ? `取消全选（已选 ${selectedChapterIds.size}）`
                : `全选（已选 ${selectedChapterIds.size}）`}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => {
                void handleBatchDeleteChapters();
              }}
              disabled={selectedChapterIds.size === 0 || batchBusy || batchRunning}
            >
              {batchBusy ? '处理中…' : `批量删除（已选 ${selectedChapterIds.size}）`}
            </button>
          </div>
          {chapters.length === 0 ? (
            <p className="empty">还没有章节</p>
          ) : (
            <ul className="list-clean stack">
              {chapters.map((item, index) => (
                <li key={item.id}>
                  <div
                    className={
                      item.id === selectedId ? 'chapter-item active' : 'chapter-item'
                    }
                    role="button"
                    tabIndex={0}
                    onClick={() => handleSelectChapter(item.id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        handleSelectChapter(item.id);
                      }
                    }}
                  >
                    <input
                      type="checkbox"
                      aria-label={`选择章节 ${item.title}`}
                      title="勾选后可批量删除"
                      checked={selectedChapterIds.has(item.id)}
                      disabled={batchBusy}
                      onClick={(event) => event.stopPropagation()}
                      onChange={() => toggleChapterSelected(item.id)}
                    />
                    <div>
                      {seqLabel(item.seq)}. {item.title}
                    </div>
                    <p className="muted">字数 {item.wordCount ?? 0}</p>
                    <div className="chapter-actions">
                      <button
                        type="button"
                        className="btn btn-ghost btn-icon"
                        aria-label={`上移 ${item.title}`}
                        title="上移"
                        disabled={index === 0 || orderBusy}
                        onClick={(event) => {
                          event.stopPropagation();
                          void handleMoveChapter(item.id, -1);
                        }}
                      >
                        ↑
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost btn-icon"
                        aria-label={`下移 ${item.title}`}
                        title="下移"
                        disabled={index === chapters.length - 1 || orderBusy}
                        onClick={(event) => {
                          event.stopPropagation();
                          void handleMoveChapter(item.id, 1);
                        }}
                      >
                        ↓
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost btn-icon"
                        aria-label={`删除 ${item.title}`}
                        title="删除"
                        disabled={orderBusy}
                        onClick={(event) => {
                          event.stopPropagation();
                          void handleDeleteChapter(item.id, item.title);
                        }}
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="btn"
            onClick={() => {
              void handleCreateChapter();
            }}
            disabled={creating}
          >
            {creating ? '创建中…' : '新建章节'}
          </button>
        </div>

        <div
          className={`panel stack workspace-column ${
            editorPrefs.focusMode ? 'panel-focus-visible' : panelClassName('editor')
          }`}
        >
          {/* 编辑器区域最顶部：最近一次保存成功的只读小字（未保存过时不显示「最后保存」前缀）。 */}
          <p className="text-xs text-gray-500" aria-live="polite">
            {lastSavedAt === null ? '尚未保存' : `最后保存：${lastSavedAt}`}
          </p>
          <div className="editor-prefs" role="group" aria-label="排版">
            <div className="editor-prefs-row">
              <span className="editor-prefs-label">字号</span>
              <div className="segmented">
                {FONT_SIZE_OPTIONS.map((size) => (
                  <button
                    key={size}
                    type="button"
                    className={editorPrefs.fontSize === size ? 'seg-btn active' : 'seg-btn'}
                    aria-pressed={editorPrefs.fontSize === size}
                    onClick={() => updateEditorPrefs({ fontSize: size })}
                  >
                    {size}px
                  </button>
                ))}
              </div>
            </div>
            <div className="editor-prefs-row">
              <span className="editor-prefs-label">行距</span>
              <div className="segmented">
                {LINE_HEIGHT_OPTIONS.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={editorPrefs.lineHeight === option ? 'seg-btn active' : 'seg-btn'}
                    aria-pressed={editorPrefs.lineHeight === option}
                    onClick={() => updateEditorPrefs({ lineHeight: option })}
                  >
                    {option.toFixed(1)}
                  </button>
                ))}
              </div>
            </div>
            <div className="editor-prefs-row">
              <span className="editor-prefs-label">专注</span>
              <button
                type="button"
                className={editorPrefs.focusMode ? 'seg-btn active' : 'seg-btn'}
                aria-pressed={editorPrefs.focusMode}
                onClick={() => updateEditorPrefs({ focusMode: !editorPrefs.focusMode })}
              >
                {editorPrefs.focusMode ? '专注模式：开（点击退出）' : '专注模式：关'}
              </button>
            </div>
          </div>
          {selectedChapter === null ? (
            <p className="empty">从左侧选择或新建章节</p>
          ) : (
            <>
              <div className="field">
                <label htmlFor="chapter-title">章节标题</label>
                <input
                  id="chapter-title"
                  className="input"
                  value={editTitle}
                  onChange={(event) => setEditTitle(event.target.value)}
                />
              </div>
              <textarea
                className="textarea editor-textarea"
                rows={18}
                style={{ fontSize: `${editorPrefs.fontSize}px`, lineHeight: editorPrefs.lineHeight }}
                ref={editorTextareaRef}
                value={editContent}
                onChange={(event) => {
                  setEditContent(event.target.value);
                  setSaveState('unsaved');
                  // 受控 textarea：onChange 后立刻读一次 selection，避免选区字数滞后。
                  syncSelectionCount(event.currentTarget);
                }}
                onSelect={(event) => syncSelectionCount(event.currentTarget)}
                onKeyUp={(event) => syncSelectionCount(event.currentTarget)}
                onMouseUp={(event) => syncSelectionCount(event.currentTarget)}
                aria-label="章节正文"
              />
              <div className="toolbar">
                <span className="muted">字数 {charCount}</span>
                <span className="badge">draft</span>
                {autoSaveText !== null ? <span className="muted">{autoSaveText}</span> : null}
              </div>
              {autoSave.status === 'error' ? (
                <div className="issue-error">自动保存失败：{autoSave.message}</div>
              ) : null}
              <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    void saveChapter();
                  }}
                  disabled={saving}
                >
                  {saving ? '保存中…' : '保存'}
                </button>
              </div>
              <div className="stack">
                <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
                  <button
                    type="button"
                    className="btn"
                    onClick={() => {
                      void handleReview();
                    }}
                    disabled={!canReview || genRunning || reviewing}
                  >
                    {reviewing ? '检查中…' : 'AI 检查'}
                  </button>
                  <button
                    type="button"
                    className="btn"
                    onClick={() => {
                      const next = !showRevisions;
                      setShowRevisions(next);
                      if (next) void loadRevisions();
                    }}
                    disabled={selectedId === null || revisionsLoading}
                  >
                    {showRevisions ? '收起历史版本' : '历史版本'}
                  </button>
                </div>
                {reviewing ? <p className="muted">检查中…</p> : null}
                {reviewError !== null ? <div className="issue-error">{reviewError}</div> : null}
                {hasReviewResult ? (
                  <>
                    {reviewSummary !== null && reviewSummary !== '' ? (
                      <p className="muted">{reviewSummary}</p>
                    ) : null}
                    {reviewIssues.length === 0 ? (
                      <p className="muted">未发现问题</p>
                    ) : (
                      reviewIssues.map((issue, index) => (
                        <div
                          className={issue.level === 'error' ? 'issue-error' : 'issue-warn'}
                          key={`review-${issue.level}-${index}`}
                        >
                          <p className="review-quote">「{issue.quote}」</p>
                          <p>{issue.suggestion}</p>
                        </div>
                      ))
                    )}
                  </>
                ) : null}
              </div>

              {showRevisions ? (
                <div className="panel stack">
                  <div className="toolbar" style={{ justifyContent: 'space-between' }}>
                    <h2 style={{ margin: 0 }}>历史版本</h2>
                    <button
                      type="button"
                      className="btn"
                      onClick={() => {
                        void loadRevisions();
                      }}
                      disabled={revisionsLoading}
                    >
                      {revisionsLoading ? '刷新中…' : '刷新'}
                    </button>
                  </div>
                  {revisions.length === 0 ? (
                    <p className="muted">{revisionsLoading ? '加载中…' : '暂无历史版本'}</p>
                  ) : (
                    revisions.map((revision) => (
                      <button
                        key={`revision-${revision.id}`}
                        type="button"
                        className="btn"
                        onClick={() => {
                          void handleOpenRevision(revision);
                        }}
                        style={{ display: 'block', width: '100%', textAlign: 'left' }}
                      >
                        <span className="muted">{formatRevisionTime(revision.createdAt)}</span>
                        <span className="badge">{revisionSourceLabel(revision.source)}</span>
                        <span className="muted">{revision.wordCount} 字</span>
                        {revision.preview !== '' ? (
                          <span className="muted" style={{ display: 'block' }}>
                            {revision.preview}
                          </span>
                        ) : null}
                      </button>
                    ))
                  )}
                  {revisionPreview !== null ? (
                    <div className="stack">
                      <div className="toolbar" style={{ justifyContent: 'space-between' }}>
                        <span className="muted">
                          {formatRevisionTime(revisionPreview.createdAt)} ·{' '}
                          {revisionSourceLabel(revisionPreview.source)}
                          {revisionPreview.wordCount !== null
                            ? ` · ${revisionPreview.wordCount} 字`
                            : ''}
                        </span>
                        <button
                          type="button"
                          className="btn"
                          onClick={() => setRevisionPreview(null)}
                        >
                          关闭预览
                        </button>
                      </div>
                      <textarea
                        className="textarea"
                        rows={12}
                        readOnly
                        value={revisionPreview.content ?? ''}
                        aria-label="历史版本正文预览"
                      />
                      <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => {
                            void handleRestoreRevision(revisionPreview);
                          }}
                          disabled={restoringRevisionId !== null}
                        >
                          {restoringRevisionId === revisionPreview.id ? '恢复中…' : '恢复此版本'}
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}

              <div className="generate-box">
                <h2>AI 生成</h2>
                <div className="field">
                  <label htmlFor="generate-instruction">写作要求</label>
                  <input
                    id="generate-instruction"
                    className="input"
                    placeholder="例如：写一场雨中的追逐戏"
                    value={instruction}
                    onChange={(event) => setInstruction(event.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="generate-target">目标字数</label>
                  <input
                    id="generate-target"
                    className="input"
                    type="number"
                    min={100}
                    step={100}
                    value={targetWords}
                    onChange={(event) => setTargetWords(event.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="generate-mode">生成方式</label>
                  <select
                    id="generate-mode"
                    className="input"
                    value={mode}
                    onChange={(event) =>
                      setMode(event.target.value === 'replace' ? 'replace' : 'append')
                    }
                  >
                    <option value="append">续写（追加到已有正文后）</option>
                    <option value="replace">重写（覆盖已有正文）</option>
                  </select>
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    if (genRunning) {
                      handleStopGenerate();
                    } else {
                      void handleGenerateChapter();
                    }
                  }}
                  disabled={reviewing || batchRunning}
                >
                  {genRunning ? '停止' : '生成'}
                </button>
              </div>
              <div className="editor-statusbar" role="status" aria-live="polite">
                <span className="editor-statusbar-item">本章 {charCount} 字</span>
                {selectionCount > 0 ? (
                  <span className="editor-statusbar-item">已选 {selectionCount} 字</span>
                ) : null}
                <span className={`editor-statusbar-save editor-statusbar-save-${saveState}`}>
                  <span className="editor-statusbar-dot" aria-hidden="true" />
                  {saveStateLabel}
                </span>
              </div>
            </>
          )}
        </div>

        <div className={`right-column stack ${panelClassName('bible')}`}>
        <div
          className={`panel stack ${
            editorPrefs.focusMode ? 'panel-focus-hidden' : ''
          }`}
        >
          <h2>润色</h2>
          <div className="field">
            <label htmlFor="polish-mode">润色方式</label>
            <select
              id="polish-mode"
              className="input"
              value={polishMode}
              onChange={(event) => {
                const next = event.target.value;
                setPolishMode(next === 'condense' ? 'condense' : next === 'expand' ? 'expand' : 'polish');
              }}
              disabled={polishRunning}
            >
              <option value="polish">润色（优化措辞，不改情节）</option>
              <option value="condense">精简（压缩篇幅，保留关键信息）</option>
              <option value="expand">扩写（补充细节，情节不变）</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="polish-instruction">额外要求</label>
            <input
              id="polish-instruction"
              className="input"
              placeholder="可选，例如：语气更冷峻，保留全部对话"
              value={polishInstruction}
              onChange={(event) => setPolishInstruction(event.target.value)}
              disabled={polishRunning}
            />
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              if (polishRunning) {
                handleCancelPolish();
              } else {
                void handleStartPolish();
              }
            }}
            disabled={selectedId === null || polishApplying}
          >
            {polishRunning ? '取消润色' : '润色'}
          </button>

          {polishError !== null ? <div className="issue-error">{`润色失败：${polishError}`}</div> : null}

          {polishOutput !== '' || polishRunning ? (
            <div className="stack">
              <p className="muted">
                {polishRunning ? '正在生成润色预览…' : `润色预览（约 ${polishOutput.length} 字）`}
              </p>
              <textarea className="textarea" rows={14} readOnly value={polishOutput} />
              {polishRunning ? null : (
                <div className="stack">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      void handleApplyPolish();
                    }}
                    disabled={polishApplying || polishOutput.trim() === ''}
                  >
                    {polishApplying ? '应用中…' : '应用'}
                  </button>
                  <button
                    type="button"
                    className="btn"
                    onClick={() => {
                      setPolishOutput('');
                      setPolishError(null);
                      setPolishApplied(false);
                    }}
                    disabled={polishApplying}
                  >
                    取消
                  </button>
                  {polishApplied ? (
                    <button
                      type="button"
                      className="btn"
                      onClick={() => {
                        void handleUndoPolish();
                      }}
                      disabled={polishApplying}
                    >
                      撤销
                    </button>
                  ) : null}
                </div>
              )}
            </div>
          ) : null}
        </div>

        <div className="panel stack">
          <h2>设定集</h2>
          {bible.length === 0 ? (
            <p className="empty">还没有设定</p>
          ) : (
            <ul className="list-clean stack">
              {bible.map((item) => (
                <li key={item.id} className="bible-list-item">
                  <div>{bibleHead(item)}</div>
                  {item.content !== null && item.content.trim() !== '' ? (
                    <p className="muted">{bibleSnippet(item.content)}</p>
                  ) : null}
                  <div>
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={() => {
                        void handleDeleteBible(item.id);
                      }}
                    >
                      删除
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <div className="field">
            <label htmlFor="bible-category">分类</label>
            <input
              id="bible-category"
              className="input"
              placeholder="角色 / 地点 / 物件"
              value={bibleCategory}
              onChange={(event) => setBibleCategory(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="bible-title">标题</label>
            <input
              id="bible-title"
              className="input"
              placeholder="设定名"
              value={bibleTitle}
              onChange={(event) => setBibleTitle(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="bible-content">内容</label>
            <textarea
              id="bible-content"
              className="textarea"
              rows={3}
              placeholder="这条设定的具体描述"
              value={bibleContent}
              onChange={(event) => setBibleContent(event.target.value)}
            />
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              void handleAddBible();
            }}
            disabled={addingBible}
          >
            {addingBible ? '添加中…' : '添加'}
          </button>

          <h2>体检</h2>
          <button
            type="button"
            className="btn"
            onClick={() => {
              void handleCheck();
            }}
            disabled={checking}
          >
            {checking ? '检查中…' : '开始检查'}
          </button>
          {checkStats === null ? null : (
            <dl className="check-stats">
              <div>
                <dt>章节数</dt>
                <dd>{checkStats.chapterCount}</dd>
              </div>
              <div>
                <dt>总字数</dt>
                <dd>{checkStats.totalWords}</dd>
              </div>
              <div>
                <dt>大纲覆盖率</dt>
                <dd>{formatCoverage(checkStats.outlineCoverage)}</dd>
              </div>
              <div>
                <dt>LLM 调用次数</dt>
                <dd>{checkStats.llmCalls}</dd>
              </div>
            </dl>
          )}
          {checkIssues.length === 0 ? (
            checkStats === null ? null : (
              <p className="muted">没有发现问题</p>
            )
          ) : (
            <div className="stack">
              {checkIssues.map((issue, index) => (
                <div
                  className={issue.level === 'error' ? 'issue-error' : 'issue-warn'}
                  key={`${issue.level}-${index}`}
                >
                  {issue.message}
                </div>
              ))}
            </div>
          )}
          <h2>创作助手</h2>
          <div className="stack" style={{ gap: '0.5rem' }}>
            {assistMessages.length === 0 ? (
              <p className="muted">问问助手：下一章该怎么写？</p>
            ) : (
              assistMessages.map((message, index) => (
                <div
                  key={`assist-${index}`}
                  className={message.role === 'user' ? 'assistant-msg user' : 'assistant-msg bot'}
                >
                  {message.content === '' ? '…' : message.content}
                </div>
              ))
            )}
            {assistError === null ? null : <div className="issue-error">{assistError}</div>}
            <textarea
              className="textarea"
              rows={3}
              placeholder="问问助手：下一章该怎么写？"
              value={assistInput}
              onChange={(event) => setAssistInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void handleAssistSend();
                }
              }}
            />
            <div className="toolbar" style={{ justifyContent: 'flex-start', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  void handleAssistSend();
                }}
                disabled={assistRunning}
              >
                {assistRunning ? '思考中…' : '发送'}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  setAssistMessages([]);
                  setAssistError(null);
                }}
                disabled={assistRunning}
              >
                清空
              </button>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}
