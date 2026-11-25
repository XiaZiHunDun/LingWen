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

type GenerateMode = 'append' | 'replace';

const DEFAULT_TARGET_WORDS = 1200;

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

function seqLabel(seq: number | null): string {
  return seq === null ? '-' : String(seq);
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

  const selectedChapter = chapters.find((item) => item.id === selectedId) ?? null;
  const charCount = editContent.replace(/\s/g, '').length;

  const showNotice = useCallback((text: string) => {
    setNotice(text);
    if (noticeTimer.current !== null) window.clearTimeout(noticeTimer.current);
    noticeTimer.current = window.setTimeout(() => setNotice(null), 3000);
  }, []);

  useEffect(
    () => () => {
      if (noticeTimer.current !== null) window.clearTimeout(noticeTimer.current);
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

  // 切换选中章节时同步编辑态，避免串内容。
  useEffect(() => {
    if (selectedChapter === null) {
      setEditTitle('');
      setEditContent('');
      return;
    }
    setEditTitle(selectedChapter.title);
    setEditContent(selectedChapter.content ?? '');
  }, [selectedChapter]);

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

  const handleSave = async () => {
    if (selectedChapter === null) return;
    setSaving(true);
    setActionError(null);
    try {
      const res = await fetch(`/api/chapters/${selectedChapter.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editTitle, content: editContent }),
      });
      if (!res.ok) throw new Error(await readErrorMessage(res));
      await refreshChapters();
      setSelectedId(selectedChapter.id);
      showNotice('已保存');
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setSaving(false);
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

    setGenRunning(true);
    setActionError(null);
    if (mode === 'replace') setEditContent('');

    try {
      const res = await fetch(`/api/chapters/${chapterId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
      setEditTitle(detail.chapter.title);
      setEditContent(detail.chapter.content ?? '');
      showNotice(`生成完成，字数 ${detail.chapter.wordCount ?? 0}`);
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setGenRunning(false);
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
          <span className="badge">{book?.genre ?? '未分类'}</span>
        </div>
      </div>

      {actionError !== null ? <div className="issue-error">{actionError}</div> : null}

      <div className="workspace-grid">
        <div className="panel stack">
          <h2>大纲</h2>
          {outlines.length === 0 ? (
            <p className="empty">还没有大纲</p>
          ) : (
            <div className="stack">
              {outlines.map((item) => (
                <div className="outline-item" key={item.id}>
                  <div>
                    {seqLabel(item.seq)}. {item.title}
                  </div>
                  {item.summary !== null && item.summary !== '' ? (
                    <p className="muted">{item.summary}</p>
                  ) : null}
                </div>
              ))}
            </div>
          )}
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
              {chapters.map((item) => (
                <li key={item.id}>
                  <div
                    className={
                      item.id === selectedId ? 'chapter-item active' : 'chapter-item'
                    }
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedId(item.id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        setSelectedId(item.id);
                      }
                    }}
                  >
                    <div>
                      {seqLabel(item.seq)}. {item.title}
                    </div>
                    <p className="muted">字数 {item.wordCount ?? 0}</p>
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
              </div>
              <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    void handleSave();
                  }}
                  disabled={saving}
                >
                  {saving ? '保存中…' : '保存'}
                </button>
              </div>
              {notice !== null ? <div className="notice">{notice}</div> : null}

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
                    void handleGenerateChapter();
                  }}
                  disabled={genRunning}
                >
                  {genRunning ? '生成中…' : '生成'}
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
        </div>
      </div>
    </div>
  );
}
