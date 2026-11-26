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

  // AI 生成正文：流式读取，边收边写进编辑区；结束后回读章节同步字数与列表。
  const handleGenerateChapter = async () => {
    if (selectedChapter === null) return;
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

      <div className="workspace-grid">
        <div className="panel stack">
          <h2>大纲</h2>
          {outlineRows.length === 0 ? (
            <p className="empty">还没有大纲</p>
          ) : (
            <div className="stack">
              {outlineRows.map((row) => (
                <div className="outline-item" key={row.key}>
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

          <h2>章节</h2>
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

        <div className="panel stack">
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
                className="textarea"
                rows={18}
                value={editContent}
                onChange={(event) => setEditContent(event.target.value)}
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
              {notice !== null ? <div className="notice">{notice}</div> : null}

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
                  disabled={reviewing}
                >
                  {genRunning ? '停止' : '生成'}
                </button>
              </div>
            </>
          )}
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
  );
}
