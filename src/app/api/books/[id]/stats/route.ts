import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, listChapters, listOutlines, listBible } from '@/lib/repo.js';

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 章节 wordCount 求和：非 number / 非有限数一律按 0 计。 */
function sumWords(chapters: ReadonlyArray<Record<string, unknown>>): number {
  let total = 0;
  for (const chapter of chapters) {
    const wordCount = chapter.wordCount;
    if (typeof wordCount === 'number' && Number.isFinite(wordCount)) {
      total += wordCount;
    }
  }
  return total;
}

/** 取字符串时间戳里的最大者（直接字符串比较），全无 string 时回 null。 */
function latestTimestamp(candidates: ReadonlyArray<unknown>): string | null {
  let latest: string | null = null;
  for (const candidate of candidates) {
    if (typeof candidate !== 'string') continue;
    if (latest === null || candidate > latest) {
      latest = candidate;
    }
  }
  return latest;
}

/** GET /api/books/[id]/stats —— 书籍的聚合统计。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    const book = getBook(bookId);
    if (book === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }

    const chapters = listChapters(bookId);
    const outlines = listOutlines(bookId);
    const bible = listBible(bookId);

    const stats = {
      chapterCount: chapters.length,
      totalWords: sumWords(chapters),
      outlineCount: outlines.length,
      bibleCount: bible.length,
      lastUpdatedAt: latestTimestamp([
        book.updatedAt,
        ...chapters.map((chapter) => chapter.updatedAt),
      ]),
    };

    return NextResponse.json({ stats });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
