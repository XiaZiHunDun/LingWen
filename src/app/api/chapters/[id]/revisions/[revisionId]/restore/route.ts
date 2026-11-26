import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import {
  createChapterRevision,
  getChapter,
  getChapterRevision,
  pruneChapterRevisions,
  recordWritingDelta,
  restoreChapterRevision,
} from '@/lib/repo.js';
import { countWords } from '@/lib/wordcount.js';

/** 每个章节保留的历史版本条数。 */
const KEEP_REVISIONS = 20;

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 版本行所属章节 id 归一为数字；无法归一返回 null。 */
function revisionChapterId(value: unknown): number | null {
  const num = Number(value);
  if (!Number.isFinite(num) || !Number.isInteger(num)) return null;
  return num;
}

/**
 * POST /api/chapters/[id]/revisions/[revisionId]/restore —— 把某个历史版本恢复为章节正文。
 *
 * 顺序：先把当前正文存为 source='pre-restore' 快照 → 再静默回填 → 最后裁剪历史。
 */
export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string; revisionId: string }> },
) {
  try {
    initDb();
    const { id, revisionId } = await params;
    const chapterId = parseId(id);
    if (chapterId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    const chapter = getChapter(chapterId);
    if (chapter === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }
    const revision = getChapterRevision(revisionId);
    if (revision === undefined || revisionChapterId(revision.chapterId) !== chapterId) {
      return NextResponse.json({ error: '版本不存在' }, { status: 404 });
    }

    // 1) 备份当前正文，避免恢复动作本身不可逆。
    const currentContent = typeof chapter.content === 'string' ? chapter.content : '';
    if (currentContent.trim() !== '') {
      createChapterRevision({
        chapterId,
        content: currentContent,
        source: 'pre-restore',
      });
    }

    // 写作日历：恢复前按正文实算一次字数，不信任 word_count 列。
    const beforeWords = countWords(currentContent);

    // 2) 回填历史版本正文。
    const restored = restoreChapterRevision(revisionId);
    if (restored === undefined) {
      return NextResponse.json({ error: '版本不存在' }, { status: 404 });
    }

    // 写作日历：恢复带来的字数净增量（0 时 recordWritingDelta 自动忽略）。
    const afterWords = countWords(typeof restored.content === 'string' ? restored.content : '');
    const delta = afterWords - beforeWords;
    if (delta !== 0) {
      recordWritingDelta({
        bookId: typeof chapter.bookId === 'number' ? chapter.bookId : null,
        chapterId,
        deltaWords: delta,
      });
    }

    // 3) 裁剪历史。
    pruneChapterRevisions(chapterId, KEEP_REVISIONS);

    return NextResponse.json({ chapter: restored });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
