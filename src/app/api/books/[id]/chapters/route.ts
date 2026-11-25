import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, listChapters, createChapter, updateChapter } from '@/lib/repo.js';
import { countWords } from '@/lib/wordcount.js';

/** 可选的字符串字段：非字符串一律按 null 处理。 */
function optionalString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** 可选的有限数字字段：非有限数 / 非数字 / NaN 一律按 null 处理。 */
function optionalNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 取已有章节里最大的 seq（没有则 0），用于自动生成新 seq。 */
function maxSeq(rows: Array<Record<string, unknown>>): number {
  let max = 0;
  for (const row of rows) {
    const seq = row.seq;
    if (typeof seq === 'number' && Number.isFinite(seq) && seq > max) {
      max = Math.floor(seq);
    }
  }
  return max;
}

/** GET /api/books/[id]/chapters —— 列出某本书的全部章节。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    if (getBook(bookId) === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }
    return NextResponse.json({ chapters: listChapters(bookId) });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** POST /api/books/[id]/chapters —— 为某本书新建一个章节（wordCount 由服务端计算）。 */
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }

    if (getBook(bookId) === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;

    const existing = listChapters(bookId);
    // seq 缺省（未提供 / null / 非有限数 / NaN）时取现有最大 seq + 1；空数组则为 1。
    const providedSeq = optionalNumber(body.seq);
    const seq = providedSeq === null ? maxSeq(existing) + 1 : providedSeq;

    // content 非字符串时按空串处理；wordCount 一律由服务端计算，忽略客户端传值。
    const content = typeof body.content === 'string' ? body.content : '';
    const wordCount = countWords(content);

    const created: Record<string, unknown> | undefined = createChapter({
      bookId,
      outlineId: optionalNumber(body.outlineId),
      seq,
      title: optionalString(body.title),
      summary: optionalString(body.summary),
      content,
      status: optionalString(body.status),
    });

    if (created === undefined) {
      throw new Error('创建章节失败：createChapter 未返回有效行');
    }
    const createdId = created.id;
    if (typeof createdId !== 'number' || !Number.isFinite(createdId)) {
      throw new Error('创建章节失败：新建行缺少有效 id');
    }

    // 建表语句里 word_count 默认 0，这里按正文实际字数补写。
    const updated = updateChapter(createdId, { wordCount });
    const chapter = updated === undefined ? created : updated;

    return NextResponse.json({ chapter }, { status: 201 });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
