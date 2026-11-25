'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';

/** 后端返回的书籍精简结构。 */
interface Book {
  id: number;
  title: string;
  genre: string | null;
  summary: string | null;
  style: string | null;
  updatedAt: string | null;
}

/** 从任意 JSON 值里安全取出错误文案。 */
function readError(payload: unknown, fallback: string): string {
  if (payload !== null && typeof payload === 'object' && 'error' in payload) {
    const value = (payload as { error?: unknown }).error;
    if (typeof value === 'string' && value.trim() !== '') return value;
  }
  return fallback;
}

export default function BookshelfPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
