import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';
import { getBook, updateBook } from '@/lib/repo.js';

/** 可选的字符串字段：非字符串一律按 null 存储。 */
function optionalString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** GET /api/books/[id] —— 取单本书。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = Number(id);
    if (Number.isNaN(bookId)) {
      return NextResponse.json({ error: 'id 必须是数字' }, { status: 400 });
    }
    const book = getBook(bookId);
    if (book === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }
    return NextResponse.json({ book });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** PATCH /api/books/[id] —— 局部更新 title/genre/summary/style。 */
export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = Number(id);
    if (Number.isNaN(bookId)) {
      return NextResponse.json({ error: 'id 必须是数字' }, { status: 400 });
    }

    const raw: unknown = await req.json();
    const body: Record<string, unknown> =
      raw !== null && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};

    const patch: {
      title?: string;
      genre?: string | null;
      summary?: string | null;
      style?: string | null;
    } = {};
    if (Object.prototype.hasOwnProperty.call(body, 'title')) {
      const title = body.title;
      if (typeof title !== 'string' || title.trim() === '') {
        return NextResponse.json({ error: 'title 必填' }, { status: 400 });
      }
      patch.title = title;
    }
    if (Object.prototype.hasOwnProperty.call(body, 'genre')) patch.genre = optionalString(body.genre);
    if (Object.prototype.hasOwnProperty.call(body, 'summary')) {
      patch.summary = optionalString(body.summary);
    }
    if (Object.prototype.hasOwnProperty.call(body, 'style')) patch.style = optionalString(body.style);

    if (getBook(bookId) === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }

    const book = updateBook(bookId, patch);
    if (book === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }
    return NextResponse.json({ book });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** DELETE /api/books/[id] —— 删除一本书（子表由外键 ON DELETE CASCADE 清理）。 */
export async function DELETE(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = Number(id);
    if (Number.isNaN(bookId)) {
      return NextResponse.json({ error: 'id 必须是数字' }, { status: 400 });
    }
    if (getBook(bookId) === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }
    getDb().prepare('DELETE FROM books WHERE id = ?').run(bookId);
    return NextResponse.json({ ok: true });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
