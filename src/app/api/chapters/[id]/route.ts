import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';
import { getChapter, updateChapter } from '@/lib/repo.js';
import { countWords } from '@/lib/wordcount.js';

/** PATCH 允许写入的字段白名单（其余字段一律忽略）。 */
const PATCH_FIELDS = ['title', 'content', 'summary', 'status', 'outlineId', 'seq'] as const;

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

/** GET /api/chapters/[id] —— 读取单个章节。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
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
    return NextResponse.json({ chapter });
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
    if (getChapter(chapterId) === undefined) {
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

    // 正文变化时重算字数；客户端传入的 wordCount 一律忽略（不在白名单内）。
    if (typeof body.content === 'string') {
      patch.wordCount = countWords(body.content);
    }

    const updated = updateChapter(chapterId, patch);
    if (updated === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }
    return NextResponse.json({ chapter: updated });
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
    if (getChapter(chapterId) === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
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
