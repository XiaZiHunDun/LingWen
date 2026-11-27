import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { parseMarkdownBook } from '@/lib/book-import.js';
import { createBookWithChapters } from '@/lib/repo.js';

/**
 * POST /api/books/import/markdown —— 把一份 Markdown 按标题拆章后导入成一本新书。
 *
 * 请求体：{ markdown: string, filename?: string }
 *
 * 处理要点（与 /api/books/import/json 保持一致的错误码与响应形状）：
 *   1. 请求体必须是 JSON 对象，markdown 必须是字符串且去空白后非空，否则 400；
 *   2. 解析全部交给纯函数 parseMarkdownBook（本路由不做任何 Markdown 逻辑），
 *      解析抛错 → 400；
 *   3. 落库走 repo.createBookWithChapters（单事务，word_count 用 countWords 口径）；
 *   4. 成功返回 { id, chapterCount }，与书架前端现有取数形状对齐（201）；
 *   5. 其余异常（含 DB）→ 500。
 */

/** 未知名 JSON 值的对象收窄。 */
type JsonObject = Record<string, unknown>;

/** 请求体对象收窄：非对象（含数组、null）返回 null。 */
function asObject(value: unknown): JsonObject | null {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return null;
  return value as JsonObject;
}

/** 统一 400 返回。 */
function badRequest(message: string) {
  return NextResponse.json({ error: message }, { status: 400 });
}

export async function POST(req: Request) {
  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return badRequest('请求体必须是合法 JSON');
  }

  const body = asObject(raw);
  if (body === null) {
    return badRequest('请求体必须是 JSON 对象');
  }

  const markdown = body.markdown;
  if (typeof markdown !== 'string') {
    return badRequest('markdown 必须是字符串');
  }
  if (markdown.trim() === '') {
    return badRequest('markdown 不能为空');
  }

  const filename = typeof body.filename === 'string' ? body.filename : undefined;

  /** @type {ReturnType<typeof parseMarkdownBook>} */
  let parsed: ReturnType<typeof parseMarkdownBook>;
  try {
    parsed = parseMarkdownBook(markdown, { filename });
  } catch (err) {
    return badRequest(`Markdown 解析失败：${err instanceof Error ? err.message : String(err)}`);
  }

  try {
    initDb();
    const { book, chapters } = createBookWithChapters({
      title: parsed.book.title,
      genre: parsed.book.genre,
      summary: parsed.book.summary,
      style: null,
      chapters: parsed.chapters,
    });
    return NextResponse.json(
      { id: Number(book.id), chapterCount: chapters.length },
      { status: 201 },
    );
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
