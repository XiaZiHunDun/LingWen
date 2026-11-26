import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getChapter, getChapterRevision } from '@/lib/repo.js';

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

/** GET /api/chapters/[id]/revisions/[revisionId] —— 读取单条历史版本全文。 */
export async function GET(
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
    if (getChapter(chapterId) === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }
    const revision = getChapterRevision(revisionId);
    if (revision === undefined || revisionChapterId(revision.chapterId) !== chapterId) {
      return NextResponse.json({ error: '版本不存在' }, { status: 404 });
    }
    return NextResponse.json({ revision });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
