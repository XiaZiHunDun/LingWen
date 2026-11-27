/**
 * POST /api/books/[id]/duplicate —— 复制一本作品。
 *
 * 返回新书 id 与 chapters / outlines / bible 的复制条数：
 *   { id, title, chapters, outlines, bible }
 *
 * 状态码：
 *   400 —— id 不是正整数
 *   404 —— 原书不存在（repo 抛 NotFoundError）
 *   500 —— 其它异常
 */

import { initDb } from '@/lib/db.js';
import { NotFoundError, duplicateBook } from '../../../../../lib/book-copy.js';

export const dynamic = 'force-dynamic';

/** 解析并校验路径参数 id。 */
function parseId(raw: string | undefined): number | null {
  if (typeof raw !== 'string' || raw.trim() === '') return null;
  const id = Number(raw);
  if (!Number.isInteger(id) || id <= 0) return null;
  return id;
}

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id: rawId } = await params;
  const id = parseId(rawId);
  if (id === null) {
    return Response.json({ error: '非法的书籍 id' }, { status: 400 });
  }

  try {
    initDb();
    const result = duplicateBook(id);
    return Response.json(result, { status: 201 });
  } catch (error) {
    if (error instanceof NotFoundError) {
      return Response.json({ error: '书籍不存在' }, { status: 404 });
    }
    return Response.json({ error: '复制作品失败' }, { status: 500 });
  }
}
