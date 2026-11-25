import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { deleteBible } from '@/lib/repo.js';

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
