import { initDb } from '@/lib/db.js';
import { getBookExport } from '@/lib/repo.js';
import { buildBookExport } from '@/lib/book-export.js';

/** 支持的导出格式。 */
type ExportFormat = 'md' | 'txt';

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** JSON 错误响应。 */
function jsonError(message: string, status: number): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}

/**
 * GET /api/books/[id]/export?format=md|txt —— 导出整本书。
 *
 * 数据聚合交给 repo.getBookExport（book + 按 seq ASC, id ASC 的章节 + 章数 + 总字数），
 * 文本拼装交给 book-export.buildBookExport，路由层只做参数校验与响应封装。
 */
export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  initDb();
  try {
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return jsonError('id 非法：必须是数字', 400);
    }

    const aggregate = getBookExport(bookId);
    if (aggregate === undefined) {
      return jsonError('书籍不存在', 404);
    }

    const rawFormat = new URL(req.url).searchParams.get('format');
    // 非法值（含未知值）一律回落到 md。
    const format: ExportFormat = rawFormat === 'txt' ? 'txt' : 'md';

    const { body, contentType, filename } = buildBookExport(
      { book: aggregate.book, chapters: aggregate.chapters },
      format,
    );

    return new Response(body, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `attachment; filename*=UTF-8''${filename}`,
      },
    });
  } catch (err) {
    return jsonError(err instanceof Error ? err.message : String(err), 500);
  }
}
