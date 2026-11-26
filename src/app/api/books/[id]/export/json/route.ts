import { initDb } from '@/lib/db.js';
import { getBook, listBible, listChapters, listOutlines } from '@/lib/repo.js';

/**
 * GET /api/books/[id]/export/json —— 导出整本书的 JSON 快照（version 1）。
 *
 * 快照结构（供 POST /api/books/import/json 反向导入）：
 *   { version: 1, exportedAt, book: { title, genre, summary, style },
 *     bible: [{ category, title, content }],
 *     outlines: [{ id, seq, title, summary, status }],
 *     chapters: [{ id, outlineId, seq, title, content, wordCount, summary, status }] }
 *
 * 注意：
 *   1. 不导出旧书 id / bookId / llm_logs / chapter_revisions；导入方自行重建 id 映射。
 *   2. 全部字段做类型收窄，非字符串字段按 null 保留，保证快照是纯 JSON。
 */

/** 行对象（repo 已转 camelCase，值类型未知）。 */
type Row = Record<string, unknown>;

/** 统一 JSON 响应头：显式声明 charset=utf-8。 */
const JSON_HEADERS = { 'Content-Type': 'application/json; charset=utf-8' } as const;

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 可空字符串字段：非字符串一律 null。 */
function nullableString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** 可空数字字段：非有限数字一律 null。 */
function nullableNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  return null;
}

/** 标题字段：空串时给出兜底文案（仅用于文件名）。 */
function titleOr(value: unknown, fallback: string): string {
  const raw = nullableString(value);
  const trimmed = raw === null ? '' : raw.trim();
  return trimmed === '' ? fallback : trimmed;
}

/** 生成快照中的 bible 项。 */
function toBibleItem(row: Row): Row {
  return {
    category: nullableString(row.category),
    title: nullableString(row.title),
    content: nullableString(row.content),
  };
}

/** 生成快照中的 outlines 项。 */
function toOutlineItem(row: Row): Row {
  return {
    id: nullableNumber(row.id),
    seq: nullableNumber(row.seq),
    title: nullableString(row.title),
    summary: nullableString(row.summary),
    status: nullableString(row.status),
  };
}

/** 生成快照中的 chapters 项（不含 bookId）。 */
function toChapterItem(row: Row): Row {
  return {
    id: nullableNumber(row.id),
    outlineId: nullableNumber(row.outlineId),
    seq: nullableNumber(row.seq),
    title: nullableString(row.title),
    content: nullableString(row.content),
    wordCount: nullableNumber(row.wordCount),
    summary: nullableString(row.summary),
    status: nullableString(row.status),
  };
}

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return new Response(JSON.stringify({ error: 'id 非法：必须是数字' }), {
        status: 400,
        headers: JSON_HEADERS,
      });
    }

    const book = getBook(bookId);
    if (book === undefined) {
      return new Response(JSON.stringify({ error: '书籍不存在' }), {
        status: 404,
        headers: JSON_HEADERS,
      });
    }

    const snapshot = {
      version: 1,
      exportedAt: new Date().toISOString(),
      book: {
        title: nullableString(book.title),
        genre: nullableString(book.genre),
        summary: nullableString(book.summary),
        style: nullableString(book.style),
      },
      bible: listBible(bookId).map(toBibleItem),
      outlines: listOutlines(bookId).map(toOutlineItem),
      chapters: listChapters(bookId).map(toChapterItem),
    };

    const filename = `${titleOr(book.title, '未命名')}.json`;

    return new Response(JSON.stringify(snapshot, null, 2), {
      status: 200,
      headers: {
        ...JSON_HEADERS,
        'Content-Disposition': `attachment; filename*=UTF-8''${encodeURIComponent(filename)}`,
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : String(err) }),
      { status: 500, headers: JSON_HEADERS },
    );
  }
}
