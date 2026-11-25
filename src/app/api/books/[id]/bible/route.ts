import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { listBible, addBible, getBook } from '@/lib/repo.js';

/** 可选的字符串字段：非字符串一律按 null 处理。 */
function optionalString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** GET /api/books/[id]/bible —— 列出某本书的全部设定集条目。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = Number(id);
    if (Number.isNaN(bookId)) {
      return NextResponse.json({ error: 'id 非法' }, { status: 400 });
    }
    if (getBook(bookId) === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }
    return NextResponse.json({ items: listBible(bookId) });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** POST /api/books/[id]/bible —— 为某本书新增一条设定集条目。 */
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = Number(id);
    if (Number.isNaN(bookId)) {
      return NextResponse.json({ error: 'id 非法' }, { status: 400 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;

    if (getBook(bookId) === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }

    const item = addBible({
      bookId,
      category: optionalString(body.category),
      title: optionalString(body.title),
      content: optionalString(body.content),
    });
    return NextResponse.json({ item }, { status: 201 });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
