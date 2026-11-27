import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { deleteBible, getBible, updateBible } from '@/lib/repo.js';
import { normalizeBiblePatch } from '@/lib/bible.js';

/** DELETE /api/bible/[id] —— 删除一条设定集条目。 */
export async function DELETE(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bibleId = Number(id);
    if (Number.isNaN(bibleId)) {
      return NextResponse.json({ error: 'id 非法' }, { status: 400 });
    }
    const changes = deleteBible(bibleId);
    if (changes === 0) {
      return NextResponse.json({ error: '设定不存在' }, { status: 404 });
    }
    return NextResponse.json({ ok: true });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** PATCH /api/bible/[id] —— 部分更新一条设定集条目（category / title / content 任意子集）。 */
export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bibleId = Number(id);
    if (Number.isNaN(bibleId)) {
      return NextResponse.json({ error: 'id 非法' }, { status: 400 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
    const { values, error } = normalizeBiblePatch(body);
    if (error !== null) {
      return NextResponse.json({ error }, { status: 400 });
    }

    if (getBible(bibleId) === undefined) {
      return NextResponse.json({ error: '设定不存在' }, { status: 404 });
    }

    const item = updateBible(bibleId, values);
    if (item === null) {
      return NextResponse.json({ error: '设定不存在' }, { status: 404 });
    }
    return NextResponse.json({ item });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
