import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { createBook, listBooks } from '@/lib/repo.js';

/** 可选的字符串字段：非字符串一律按 null 存储。 */
function optionalString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** 书架排序白名单（与 src/lib/repo.js 的 BOOK_SORTS 保持一致）。 */
const SORT_VALUES = ['updated', 'created', 'title', 'words'] as const;

type BookSort = (typeof SORT_VALUES)[number];

/** 判断 query 参数是否为合法排序值。 */
function isBookSort(value: string): value is BookSort {
  return (SORT_VALUES as readonly string[]).includes(value);
}

/** GET /api/books —— 列出全部书籍，支持 ?sort=updated|created|title|words。 */
export async function GET(req: Request) {
  try {
    initDb();
    const sort = new URL(req.url).searchParams.get('sort');
    if (sort !== null && !isBookSort(sort)) {
      return NextResponse.json(
        {
          error: `非法的 sort 参数：${sort}（仅支持 ${SORT_VALUES.join(' / ')}）`,
        },
        { status: 400 },
      );
    }
    return NextResponse.json({ books: sort === null ? listBooks() : listBooks({ sort }) });
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
