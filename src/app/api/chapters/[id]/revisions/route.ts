import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getChapter, listChapterRevisions } from '@/lib/repo.js';

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** GET /api/chapters/[id]/revisions —— 列出某章节的历史版本（倒序，仅元信息 + 预览）。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const chapterId = parseId(id);
    if (chapterId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    if (getChapter(chapterId) === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }
    return NextResponse.json({ revisions: listChapterRevisions(chapterId) });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
