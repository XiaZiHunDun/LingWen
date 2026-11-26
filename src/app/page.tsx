'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';

/** 全局搜索结果条目（与 /api/search 返回结构一致）。 */
type SearchType = 'chapter' | 'outline' | 'bible';

interface SearchItem {
  bookId: number;
  bookTitle: string;
  type: SearchType;
  id: number;
  title: string;
  snippet: string;
}

/** 结果类型 → 中文标签。 */
const SEARCH_TYPE_LABELS: Record<SearchType, string> = {
  chapter: '章节',
  outline: '大纲',
  bible: '设定',
};

/** 从任意 JSON 值里安全取出搜索结果数组。 */
function readSearchItems(payload: unknown): SearchItem[] {
  if (payload === null || typeof payload !== 'object' || !('items' in payload)) return [];
  const raw = (payload as { items?: unknown }).items;
  if (!Array.isArray(raw)) return [];
  const items: SearchItem[] = [];
  for (const entry of raw) {
    if (entry === null || typeof entry !== 'object') continue;
    const row = entry as Record<string, unknown>;
    const type = row.type;
    if (type !== 'chapter' && type !== 'outline' && type !== 'bible') continue;
    items.push({
      bookId: Number(row.bookId),
      bookTitle: typeof row.bookTitle === 'string' ? row.bookTitle : '',
      type,
      id: Number(row.id),
      title: typeof row.title === 'string' ? row.title : '',
      snippet: typeof row.snippet === 'string' ? row.snippet : '',
    });
  }
  return items;
}

/** 后端返回的书籍精简结构。 */
interface Book {
  id: number;
  title: string;
  genre: string | null;
  summary: string | null;
  style: string | null;
  updatedAt: string | null;
}

/** 全站统计结构。 */
interface Stats {
  bookCount: number;
  chapterCount: number;
  totalWords: number;
  outlineCount: number;
  bibleCount: number;
}

/** 从任意 JSON 值里安全取出错误文案。 */
function readError(payload: unknown, fallback: string): string {
  if (payload !== null && typeof payload === 'object' && 'error' in payload) {
    const value = (payload as { error?: unknown }).error;
    if (typeof value === 'string' && value.trim() !== '') return value;
  }
  return fallback;
}

/** 从任意 JSON 值里安全取出统计数字，缺失或类型不符时返回 null。 */
function readStats(payload: unknown): Stats | null {
  if (payload === null || typeof payload !== 'object' || !('stats' in payload)) return null;
  const raw = (payload as { stats?: unknown }).stats;
  if (raw === null || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const { bookCount, chapterCount, totalWords, outlineCount, bibleCount } = source;
  if (
    typeof bookCount !== 'number' ||
    typeof chapterCount !== 'number' ||
    typeof totalWords !== 'number' ||
    typeof outlineCount !== 'number' ||
    typeof bibleCount !== 'number'
  ) {
    return null;
  }
  return { bookCount, chapterCount, totalWords, outlineCount, bibleCount };
}

export default function BookshelfPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('');
  const [summary, setSummary] = useState('');
  const [style, setStyle] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadBooks = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const res = await fetch('/api/books');
      const data: unknown = await res.json();
      if (!res.ok) {
        setError(readError(data, '加载作品列表失败'));
        return;
      }
      const list =
        data !== null && typeof data === 'object' && 'books' in data
          ? (data as { books?: unknown }).books
          : undefined;
      setBooks(Array.isArray(list) ? (list as Book[]) : []);
      setError(null);
    } catch {
      setError('加载作品列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBooks();
  }, [loadBooks]);

  useEffect(() => {
    let active = true;
    void (async (): Promise<void> => {
      try {
        const res = await fetch('/api/stats');
        if (!res.ok) {
          if (active) setStats(null);
          return;
        }
        const data: unknown = await res.json();
        if (active) setStats(readStats(data));
      } catch {
        if (active) setStats(null);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const router = useRouter();

  // 全局搜索：输入、结果、请求中、浮层开关、是否已拿到结果。
  const [searchQuery, setSearchQuery] = useState('');
  const [searchItems, setSearchItems] = useState<SearchItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchDone, setSearchDone] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchBoxRef = useRef<HTMLDivElement | null>(null);
  // 递增请求序号，丢弃过期响应，避免旧结果覆盖新结果。
  const searchSeqRef = useRef(0);

  useEffect(() => {
    const q = searchQuery.trim();
    if (q === '') {
      searchSeqRef.current += 1;
      setSearchItems([]);
      setSearchLoading(false);
      setSearchDone(false);
      setSearchOpen(false);
      return;
    }
    searchSeqRef.current += 1;
    const seq = searchSeqRef.current;
    setSearchOpen(true);
    setSearchLoading(true);
    const timer = window.setTimeout(() => {
      void (async (): Promise<void> => {
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
          if (searchSeqRef.current !== seq) return;
          if (!res.ok) {
            setSearchItems([]);
            setSearchDone(true);
            return;
          }
          const data: unknown = await res.json();
          if (searchSeqRef.current !== seq) return;
          setSearchItems(readSearchItems(data));
          setSearchDone(true);
        } catch {
          if (searchSeqRef.current !== seq) return;
          setSearchItems([]);
          setSearchDone(true);
        } finally {
          if (searchSeqRef.current === seq) setSearchLoading(false);
        }
      })();
    }, 300);
    return () => {
      window.clearTimeout(timer);
    };
  }, [searchQuery]);

  // Esc 关闭浮层；点击浮层外（不在搜索框容器内）关闭。
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') setSearchOpen(false);
    };
    const onMouseDown = (event: MouseEvent): void => {
      const box = searchBoxRef.current;
      if (box !== null && event.target instanceof Node && box.contains(event.target)) return;
      setSearchOpen(false);
    };
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('mousedown', onMouseDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('mousedown', onMouseDown);
    };
  }, []);

  function handleOpenResult(item: SearchItem): void {
    setSearchOpen(false);
    router.push(
      item.type === 'chapter' ? `/books/${item.bookId}?chapter=${item.id}` : `/books/${item.bookId}`,
    );
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (title.trim() === '') {
      setError('书名不能为空');
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch('/api/books', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          genre,
          summary,
          style,
        }),
      });
      const data: unknown = await res.json();
      if (!res.ok) {
        setError(readError(data, '新建作品失败'));
        return;
      }
      setTitle('');
      setGenre('');
      setSummary('');
      setStyle('');
      setError(null);
      await loadBooks();
    } catch {
      setError('新建作品失败');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(book: Book): Promise<void> {
    if (!window.confirm(`确定删除《${book.title}》吗？该操作不可撤销。`)) return;
    try {
      const res = await fetch(`/api/books/${book.id}`, { method: 'DELETE' });
      const data: unknown = await res.json();
      if (!res.ok) {
        setError(readError(data, '删除作品失败'));
        return;
      }
      setError(null);
      await loadBooks();
    } catch {
      setError('删除作品失败');
    }
  }

  return (
    <>
      <section className="card">
        <div className="toolbar">
          <div>
            <h1>我的书架</h1>
            <p className="muted">长篇连载从这里开始：新建一本作品，再进入工作台铺大纲、写章节。</p>
          </div>
        </div>
        <div className="field" ref={searchBoxRef} style={{ position: 'relative' }}>
          <label htmlFor="global-search">全局搜索</label>
          <input
            id="global-search"
            className="input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => {
              if (searchQuery.trim() !== '') setSearchOpen(true);
            }}
            placeholder="搜索章节标题 / 正文 / 大纲 / 设定…"
            autoComplete="off"
          />
          {searchOpen ? (
            <div
              className="card"
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: 4,
                zIndex: 50,
                maxHeight: 360,
                overflowY: 'auto',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.18)',
              }}
            >
              {searchItems.length === 0 ? (
                searchLoading || !searchDone ? (
                  <p className="muted">搜索中…</p>
                ) : (
                  <p className="muted">未找到相关内容</p>
                )
              ) : (
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {searchItems.map((item) => (
                    <li key={`${item.type}-${item.id}`}>
                      <button
                        type="button"
                        style={{
                          display: 'block',
                          width: '100%',
                          textAlign: 'left',
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'inherit',
                          padding: '8px 10px',
                        }}
                        onClick={() => handleOpenResult(item)}
                      >
                        <div>
                          <strong>{item.bookTitle}</strong>
                          {' · '}
                          {SEARCH_TYPE_LABELS[item.type]}
                          {' · '}
                          <span>{item.title}</span>
                        </div>
                        {item.snippet !== '' ? (
                          <p
                            className="muted line-clamp-2"
                            style={{
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden',
                              margin: 0,
                            }}
                          >
                            {item.snippet}
                          </p>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}
        </div>
        {stats !== null ? (
          <p className="muted">
            作品 {stats.bookCount} · 章节 {stats.chapterCount} · 总字数{' '}
            {stats.totalWords.toLocaleString('zh-CN')}
          </p>
        ) : null}
      </section>

      <section className="card">
        <h2>新建作品</h2>
        <form onSubmit={handleCreate}>
          <div className="field">
            <label htmlFor="book-title">书名（必填）</label>
            <input
              id="book-title"
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如：长夜将明"
            />
          </div>
          <div className="field">
            <label htmlFor="book-genre">题材</label>
            <input
              id="book-genre"
              className="input"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              placeholder="例如：东方玄幻"
            />
          </div>
          <div className="field">
            <label htmlFor="book-summary">简介</label>
            <textarea
              id="book-summary"
              className="textarea"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="一句话讲清故事的核心冲突"
            />
          </div>
          <div className="field">
            <label htmlFor="book-style">文风</label>
            <input
              id="book-style"
              className="input"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              placeholder="例如：冷峻短句、多对白"
            />
          </div>
          <div className="toolbar">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? '创建中…' : '新建作品'}
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <div className="toolbar">
          <h2>作品列表</h2>
          <span className="muted">共 {books.length} 本</span>
        </div>

        {error !== null ? (
          <p className="form-error">{error}</p>
        ) : null}

        {loading ? (
          <p className="muted">加载中…</p>
        ) : books.length === 0 ? (
          <p className="empty">还没有作品，先新建一本吧</p>
        ) : (
          <div className="book-grid">
            {books.map((book) => (
              <article className="book-card" key={book.id}>
                <div className="toolbar">
                  <h3>{book.title}</h3>
                  <span className="badge">{book.genre ?? '未分类'}</span>
                </div>
                <p className="muted">{book.summary ?? '暂无简介'}</p>
                <p className="muted">更新于 {book.updatedAt ?? '未知'}</p>
                <div className="toolbar">
                  <a className="btn btn-ghost" href={`/books/${book.id}`}>
                    进入工作台
                  </a>
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => {
                      void handleDelete(book);
                    }}
                  >
                    删除
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
