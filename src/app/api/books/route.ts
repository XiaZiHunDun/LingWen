import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { createBook, listBooks } from '@/lib/repo.js';

/** 可选的字符串字段：非字符串一律按 null 存储。 */
function optionalString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** GET /api/books —— 列出全部书籍。 */
export async function GET() {
  try {
    initDb();
    return NextResponse.json({ books: listBooks() });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** POST /api/books —— 新建一本书，title 必填。 */
export async function POST(req: Request) {
  try {
    initDb();
    const raw: unknown = await req.json();
    const body: Record<string, unknown> =
      raw !== null && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};

    const title = body.title;
    if (typeof title !== 'string' || title.trim() === '') {
      return NextResponse.json({ error: 'title 必填' }, { status: 400 });
    }

    const book = createBook({
      title,
      genre: optionalString(body.genre),
      summary: optionalString(body.summary),
      style: optionalString(body.style),
    });
    return NextResponse.json({ book }, { status: 201 });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
