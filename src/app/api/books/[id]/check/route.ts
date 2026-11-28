import { NextResponse } from 'next/server';
import { initDb, getDb } from '@/lib/db.js';
import { getBook, listBible, listOutlines, listChapters } from '@/lib/repo.js';
import { summarizeBibleCoverage } from '@/lib/bible-coverage.js';

/** 响应里最多回传多少条设定覆盖明细（超出截断，由前端自行提示）。 */
const MAX_BIBLE_COVERAGE = 100;

/** issue 级别。 */
type IssueLevel = 'error' | 'warn';

/** 单条体检问题。 */
interface Issue {
  level: IssueLevel;
  message: string;
}

/** 体检统计。 */
interface CheckStats {
  chapterCount: number;
  totalWords: number;
  emptyChapters: number;
  outlineCount: number;
  outlineCoverage: number;
  bibleCount: number;
  /** 至少在正文或大纲里出现过一次的设定条数。 */
  bibleUsed: number;
  /** 从未在正文和大纲里出现过的设定条数。 */
  bibleUnused: number;
  llmCalls: number;
}

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 有限数字原样返回，否则按 0 处理。 */
function finiteOrZero(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

/** 从 llm_logs 计数行里安全取出 n。 */
function pickCount(row: unknown): number {
  if (typeof row !== 'object' || row === null) return 0;
  if (!('n' in row)) return 0;
  const value = (row as { n?: unknown }).n;
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

/** 章节标题等文本字段：非字符串按空串处理。 */
function text(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

/** GET /api/books/[id]/check —— 书籍体检：返回统计与问题列表。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  initDb();
  try {
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

    const outlineIdSet = new Set<number>();
    for (const outline of outlines) {
      const outlineId = outline.id;
      if (typeof outlineId === 'number' && Number.isFinite(outlineId)) {
        outlineIdSet.add(outlineId);
      }
    }

    let totalWords = 0;
    let emptyChapters = 0;
    let coveredChapters = 0;
    for (const chapter of chapters) {
      totalWords += finiteOrZero(chapter.wordCount);
      if (text(chapter.content).trim() === '') {
        emptyChapters += 1;
      }
      const outlineId = chapter.outlineId;
      if (typeof outlineId === 'number' && outlineIdSet.has(outlineId)) {
        coveredChapters += 1;
      }
    }

    const outlineCount = outlines.length;
    const outlineCoverage =
      outlineCount === 0 ? 0 : Math.round((coveredChapters / outlineCount) * 100) / 100;

    const countRow = getDb()
      .prepare('SELECT COUNT(*) AS n FROM llm_logs WHERE book_id = ?')
      .get(bookId);
    const llmCalls = pickCount(countRow);

    const coverage = summarizeBibleCoverage({ bible, chapters, outlines });

    const stats: CheckStats = {
      chapterCount: chapters.length,
      totalWords,
      emptyChapters,
      outlineCount,
      outlineCoverage,
      bibleCount: bible.length,
      bibleUsed: coverage.usedCount,
      bibleUnused: coverage.unusedCount,
      llmCalls,
    };

    const issues: Issue[] = [];
    if (outlineCount === 0) {
      issues.push({ level: 'error', message: '还没有大纲' });
    }
    if (emptyChapters > 0) {
      issues.push({ level: 'warn', message: `${emptyChapters} 章还没有正文` });
    }
    if (outlineCoverage < 0.8 && outlineCount > 0) {
      issues.push({ level: 'warn', message: '大纲覆盖率偏低' });
    }
    if (stats.bibleCount === 0) {
      issues.push({ level: 'warn', message: '设定集为空' });
    }
    if (coverage.unusedCount > 0) {
      issues.push({
        level: 'warn',
        message: `${coverage.unusedCount} 条设定还没在正文或大纲里出现`,
      });
    }

    return NextResponse.json({
      stats,
      issues,
      bibleCoverage: coverage.items.slice(0, MAX_BIBLE_COVERAGE),
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
