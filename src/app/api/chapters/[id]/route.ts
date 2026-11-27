import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';
import { normalizeChapterStatus } from '@/lib/chapter-status.js';
import {
  createChapterRevision,
  getChapter,
  pruneChapterRevisions,
  recordWritingDelta,
  updateChapter,
} from '@/lib/repo.js';
import { countWords } from '@/lib/wordcount.js';

/** PATCH 允许写入的字段白名单（其余字段一律忽略）；status 单独校验后写入。 */
const PATCH_FIELDS = ['title', 'content', 'summary', 'outlineId', 'seq'] as const;

/** 每个章节保留的历史版本条数。 */
const KEEP_REVISIONS = 20;

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 可选的有限数字字段：非有限数 / 非数字 / NaN 一律按 null 处理。 */
function optionalNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

/** 输出用的 status：空值/非法值统一按 'draft' 输出（不改库）。 */
function outStatus(value: unknown): 'draft' | 'final' {
  return normalizeChapterStatus(value) ?? 'draft';
}

/** GET /api/chapters/[id] —— 读取单个章节。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const chapterId = parseId(id);
    if (chapterId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    const chapter = getChapter(chapterId) as Record<string, unknown> | undefined;
    if (chapter === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }
    return NextResponse.json({ chapter: { ...chapter, status: outStatus(chapter.status) } });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** PATCH /api/chapters/[id] —— 局部更新章节；含 content 时同步重算 wordCount。 */
export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const chapterId = parseId(id);
    if (chapterId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    const existing = getChapter(chapterId);
    if (existing === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;

    // 只挑白名单字段：数值字段走有限数校验，其余按字符串归一。
    const patch: {
      title?: string | null;
      content?: string | null;
      summary?: string | null;
      status?: string | null;
      outlineId?: number | null;
      seq?: number | null;
      wordCount?: number;
    } = {};

    for (const field of PATCH_FIELDS) {
      if (!Object.prototype.hasOwnProperty.call(body, field)) continue;
      const raw = body[field];
      if (field === 'outlineId' || field === 'seq') {
        patch[field] = optionalNumber(raw);
      } else {
        patch[field] = typeof raw === 'string' ? raw : null;
      }
    }

    // status：只有显式传了该字段才校验，非法值直接 400 且不落库；未传则完全不动。
    if (Object.prototype.hasOwnProperty.call(body, 'status')) {
      const normalized = normalizeChapterStatus(body.status);
      if (normalized === null) {
        return NextResponse.json(
          { error: "status 非法：仅支持 'draft' / 'final'" },
          { status: 400 },
        );
      }
      patch.status = normalized;
    }

    // 正文变化时重算字数；客户端传入的 wordCount 一律忽略（不在白名单内）。
    if (typeof body.content === 'string') {
      patch.wordCount = countWords(body.content);
    }

    // 自动快照：新正文与旧正文不同、且旧正文非空时，先把旧正文存为 manual 版本。
    const oldContent = typeof existing.content === 'string' ? existing.content : '';
    // 写作日历：新旧正文的字数净差（差为 0 时不写 writing_sessions）。
    const wordDelta =
      typeof body.content === 'string' ? (patch.wordCount ?? 0) - countWords(oldContent) : 0;
    if (
      typeof body.content === 'string' &&
      body.content !== oldContent &&
      oldContent.trim() !== ''
    ) {
      createChapterRevision({ chapterId, content: oldContent, source: 'manual' });
    }

    const updated = updateChapter(chapterId, patch);
    if (updated === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }

    // 保存成功后把字数净增量写入写作会话（差为 0 时 recordWritingDelta 自动忽略）。
    if (wordDelta !== 0) {
      recordWritingDelta({
        bookId: typeof existing.bookId === 'number' ? existing.bookId : null,
        chapterId,
        deltaWords: wordDelta,
      });
    }

    // 更新成功后再裁剪历史，每个章节只保留最近 KEEP_REVISIONS 条。
    if (typeof body.content === 'string') {
      pruneChapterRevisions(chapterId, KEEP_REVISIONS);
    }

    const updatedRow = updated as Record<string, unknown>;
    return NextResponse.json({
      chapter: { ...updatedRow, status: outStatus(updatedRow.status) },
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** DELETE /api/chapters/[id] —— 删除一个章节。 */
export async function DELETE(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const chapterId = parseId(id);
    if (chapterId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    const chapter = getChapter(chapterId);
    if (chapter === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }
    // 写作日历：删除章节按现有正文字数记一次负增量（为 0 时 recordWritingDelta 自动忽略）。
    const removedWords = countWords(typeof chapter.content === 'string' ? chapter.content : '');
    if (removedWords !== 0) {
      recordWritingDelta({
        bookId: typeof chapter.bookId === 'number' ? chapter.bookId : null,
        chapterId,
        deltaWords: -removedWords,
      });
    }
    getDb().prepare('DELETE FROM chapters WHERE id = ?').run(chapterId);
    return NextResponse.json({ ok: true });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
