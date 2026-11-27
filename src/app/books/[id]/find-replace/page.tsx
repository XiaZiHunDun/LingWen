'use client';

/**
 * 全书查找替换面板。
 *
 * 交互分两步（对齐需求里的「先预览、二次确认」）：
 *   1. 输入查找词 → 预览：哪些章节命中、各命中多少次、上下文片段；
 *   2. 填新词 → 点「替换全部」→ 再点「确认替换」→ 调后端原子替换并提示
 *      「共替换 N 处，涉及 M 章」。
 * 后端接口：POST /api/books/[id]/find-replace（mode: preview / replace + confirm）。
 */

import { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

type Snippet = { before: string; match: string; after: string };

type PreviewChapter = {
  chapterId: number;
  seq: number | null;
  title: string;
  matches: number;
  wordCount: number;
  snippets: Snippet[];
};

type PreviewResult = {
  query: string;
  totalMatches: number;
  chapterCount: number;
  chapters: PreviewChapter[];
};

type ReplaceResult = {
  message: string;
  totalMatches: number;
  chapterCount: number;
  wordCountDelta: number;
};

/** 从错误响应体里取 error 文案。 */
function extractError(data: unknown): string | null {
  if (data !== null && typeof data === 'object' && 'error' in data) {
    const value = (data as { error?: unknown }).error;
    if (typeof value === 'string' && value !== '') return value;
  }
  return null;
}

/** 替换词为空时在提示里显示得更清楚。 */
function displayWord(word: string): string {
  return word === '' ? '（空）' : word;
}

export default function FindReplacePage() {
  const params = useParams();
  const rawId = params?.id;
  const bookId = Array.isArray(rawId) ? (rawId[0] ?? '') : (rawId ?? '');

  const [query, setQuery] = useState('');
  const [replacement, setReplacement] = useState('');
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [result, setResult] = useState<ReplaceResult | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [pending, setPending] = useState<'preview' | 'replace' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const busy = pending !== null;
  const canSearch = query !== '' && !busy;

  async function post(body: Record<string, unknown>): Promise<unknown> {
    const response = await fetch(`/api/books/${bookId}/find-replace`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(extractError(data) ?? `请求失败（${response.status}）`);
    }
    return data;
  }

  async function runPreview() {
    setError(null);
    setResult(null);
    setConfirming(false);
    setPending('preview');
    try {
      const data = await post({ mode: 'preview', query });
      setPreview(data as PreviewResult);
    } catch (err) {
      setPreview(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(null);
    }
  }

  async function runReplace() {
    setError(null);
    setPending('replace');
    try {
      const data = await post({ mode: 'replace', query, replacement, confirm: true });
      const replaced = data as ReplaceResult;
      setResult(replaced);
      setConfirming(false);
      // 替换后刷新预览：命中数应归零，正文已是新词。
      const refreshed = await post({ mode: 'preview', query });
      setPreview(refreshed as PreviewResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="workspace find-replace-panel">
      <div className="toolbar">
        <div className="stack" style={{ gap: '0.35rem' }}>
          <Link href={`/books/${bookId}`}>返回书籍</Link>
          <h1 className="page-title">全书查找替换</h1>
        </div>
      </div>

      <div className="find-replace-form">
        <label className="find-replace-field">
          <span>查找</span>
          <input
            className="find-replace-input"
            value={query}
            placeholder="要查找的词"
            onChange={(event) => {
              setQuery(event.target.value);
              setPreview(null);
              setResult(null);
              setConfirming(false);
            }}
          />
        </label>
        <label className="find-replace-field">
          <span>替换为</span>
          <input
            className="find-replace-input"
            value={replacement}
            placeholder="新词（留空表示删除）"
            onChange={(event) => {
              setReplacement(event.target.value);
              setConfirming(false);
            }}
          />
        </label>
        <button
          type="button"
          className="btn"
          disabled={!canSearch}
          onClick={() => {
            void runPreview();
          }}
        >
          {pending === 'preview' ? '查找中…' : '查找（预览命中）'}
        </button>
      </div>

      {error !== null ? <div className="notice">{error}</div> : null}
      {result !== null ? (
        <div className="find-replace-result" role="status">
          {result.message}
          {result.wordCountDelta !== 0 ? `（字数净变化 ${result.wordCountDelta}）` : ''}
        </div>
      ) : null}

      {preview !== null ? (
        <div className="find-replace-preview">
          <p className="find-replace-summary">
            「{displayWord(preview.query)}」共命中 {preview.totalMatches} 处，涉及{' '}
            {preview.chapterCount} 章
          </p>

          {preview.totalMatches === 0 ? (
            <p className="find-replace-empty">全书没有找到「{displayWord(preview.query)}」。</p>
          ) : (
            <ul className="find-replace-list">
              {preview.chapters.map((chapter) => (
                <li className="find-replace-chapter" key={chapter.chapterId}>
                  <div className="find-replace-chapter-head">
                    <strong>
                      {chapter.seq === null
                        ? chapter.title
                        : `第 ${chapter.seq} 章 ${chapter.title}`}
                    </strong>
                    <span className="badge">{chapter.matches} 处</span>
                  </div>
                  <ul className="find-replace-snippets">
                    {chapter.snippets.map((snippet, index) => (
                      <li className="find-replace-snippet" key={`${chapter.chapterId}-${index}`}>
                        {snippet.before}
                        <mark>{snippet.match}</mark>
                        {snippet.after}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}

          {preview.totalMatches > 0 ? (
            confirming ? (
              <div className="find-replace-confirm">
                <p>
                  确认把「{displayWord(preview.query)}」替换为「{displayWord(replacement)}」？共{' '}
                  {preview.totalMatches} 处、涉及 {preview.chapterCount} 章，替换会为每章保存一条
                  历史版本。
                </p>
                <div className="toolbar" style={{ justifyContent: 'flex-start' }}>
                  <button
                    type="button"
                    className="btn"
                    disabled={busy}
                    onClick={() => {
                      void runReplace();
                    }}
                  >
                    {pending === 'replace' ? '替换中…' : '确认替换'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={busy}
                    onClick={() => {
                      setConfirming(false);
                    }}
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                className="btn"
                disabled={busy}
                onClick={() => {
                  setConfirming(true);
                }}
              >
                替换全部（{preview.totalMatches} 处）
              </button>
            )
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
