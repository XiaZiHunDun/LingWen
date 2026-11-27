import { NextResponse } from 'next/server';
import { previewMarkdownImport } from '@/lib/book-import.js';

/**
 * POST /api/books/import/markdown/preview —— Markdown 导入预览（只解析，不落库）。
 *
 * 请求体：{ markdown: string, filename?: string, headingLevel?: 2 | 3 }
 *
 * 校验口径与 /api/books/import/markdown 完全一致；解析全部交给 lib 的纯函数
 * previewMarkdownImport（内部复用 parseMarkdownBook），本路由不含任何 Markdown 逻辑，
 * 也不调用 initDb / 任何写库函数。
 *
 * 响应：{ book: { title, genre, summary }, chapterCount: number, chapterTitles: string[] }
 *   chapterTitles 最多前 3 章标题。
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

  const rawHeadingLevel = body.headingLevel;
  if (
    rawHeadingLevel !== undefined &&
    rawHeadingLevel !== null &&
    rawHeadingLevel !== 2 &&
    rawHeadingLevel !== 3
  ) {
    return badRequest('headingLevel 只支持 2 或 3');
  }
  const headingLevel: 2 | 3 = rawHeadingLevel === 3 ? 3 : 2;

  try {
    const preview = previewMarkdownImport(markdown, { filename, headingLevel });
    return NextResponse.json({
      book: {
        title: preview.book.title,
        genre: preview.book.genre,
        summary: preview.book.summary,
      },
      chapterCount: preview.chapterCount,
      chapterTitles: preview.chapterTitles,
    });
  } catch (err) {
    return badRequest(`Markdown 解析失败：${err instanceof Error ? err.message : String(err)}`);
  }
}
