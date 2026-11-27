import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook } from '@/lib/repo.js';
import { previewBookReplace, replaceBookText } from '@/lib/find-replace.js';

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 从请求体里取字符串字段，非字符串返回 ''。 */
function readString(source: Record<string, unknown>, key: string): string {
  const value = source[key];
  return typeof value === 'string' ? value : '';
}

/**
 * POST /api/books/[id]/find-replace —— 全书查找替换。
 *
 * 请求体：
 *   { mode: 'preview', query }                              → 只读预览（每章命中次数 + 上下文）
 *   { mode: 'replace', query, replacement, confirm: true }   → 二次确认后一键替换（原子事务）
 *
 * 预览不写库；替换必须显式带 confirm: true，缺省一律拒绝，避免误触。
 */
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
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

    const raw: unknown = await request.json().catch(() => null);
    if (raw === null || typeof raw !== 'object') {
      return NextResponse.json({ error: '请求体必须是 JSON 对象' }, { status: 400 });
    }
    const body = raw as Record<string, unknown>;
    const query = readString(body, 'query');
    if (query === '') {
      return NextResponse.json({ error: '查找词不能为空' }, { status: 400 });
    }

    const mode = readString(body, 'mode') === 'replace' ? 'replace' : 'preview';

    if (mode === 'preview') {
      const preview = previewBookReplace(bookId, query);
      return NextResponse.json({ mode: 'preview', ...preview });
    }

    if (body.confirm !== true) {
      return NextResponse.json(
        { error: '替换需要二次确认：请在请求体带上 confirm: true' },
        { status: 400 },
      );
    }

    const replacement = readString(body, 'replacement');
    const result = replaceBookText(bookId, { query, replacement });
    return NextResponse.json({ mode: 'replace', ...result });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const status = err instanceof RangeError ? 400 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
