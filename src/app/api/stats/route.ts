import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';

/** 从查询结果行里安全取出一个数字：非对象、缺字段、非有限数一律按 0 处理。 */
function pickNumber(row: unknown, key: string): number {
  if (row === null || typeof row !== 'object') return 0;
  const v = (row as Record<string, unknown>)[key];
  const n = typeof v === 'number' ? v : Number(v);
  return Number.isFinite(n) ? n : 0;
}

/** GET /api/stats —— 全局统计（书籍数 / 章节数 / 总字数 / 大纲数 / 设定条目数）。 */
export async function GET() {
  try {
    initDb();
    const db = getDb();

    const bookRow: unknown = db.prepare('SELECT COUNT(*) AS n FROM books').get();
    const chapterRow: unknown = db
      .prepare('SELECT COUNT(*) AS n, COALESCE(SUM(word_count),0) AS words FROM chapters')
      .get();
    const outlineRow: unknown = db.prepare('SELECT COUNT(*) AS n FROM outlines').get();
    const bibleRow: unknown = db.prepare('SELECT COUNT(*) AS n FROM bible').get();

    return NextResponse.json({
      stats: {
        bookCount: Number(pickNumber(bookRow, 'n')),
        chapterCount: Number(pickNumber(chapterRow, 'n')),
        totalWords: Number(pickNumber(chapterRow, 'words')),
        outlineCount: Number(pickNumber(outlineRow, 'n')),
        bibleCount: Number(pickNumber(bibleRow, 'n')),
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
