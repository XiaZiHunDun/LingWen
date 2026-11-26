import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';

export const dynamic = 'force-dynamic';

const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 50;

/** 命中位置前后的上下文宽度（字符数）。 */
const CONTEXT_CHARS = 40;
/** 未命中/仅命中标题时，退化为正文前若干字的摘要宽度。 */
const FALLBACK_CHARS = 80;

type SearchType = 'chapter' | 'outline' | 'bible';

interface SearchItem {
  bookId: number;
  bookTitle: string;
  type: SearchType;
  id: number;
  title: string;
  snippet: string;
}

/**
 * 转义 LIKE 模式里的特殊字符，配合 `ESCAPE '\'` 使用，
 * 保证用户输入的 \ % _ 只作为普通字符参与子串匹配。
 */
function escapeLike(input: string): string {
  return input.replace(/[\\%_]/g, (ch) => `\\${ch}`);
}

/** 解析 limit：默认 20，上限 50，非法值（非数字/非正/NaN/Infinity）回落默认。 */
function normalizeLimit(raw: string | null): number {
  if (raw === null) return DEFAULT_LIMIT;
  const trimmed = raw.trim();
  if (trimmed === '') return DEFAULT_LIMIT;
  const n = Number(trimmed);
  if (!Number.isFinite(n)) return DEFAULT_LIMIT;
  const int = Math.trunc(n);
  if (int < 1) return DEFAULT_LIMIT;
  return int > MAX_LIMIT ? MAX_LIMIT : int;
}

/** 从查询结果行里安全取出字符串：null/undefined 一律按空串处理。 */
function pickString(row: Record<string, unknown>, key: string): string {
  const v = row[key];
  if (v === null || v === undefined) return '';
  return typeof v === 'string' ? v : String(v);
}

/** 从查询结果行里安全取出数字：缺字段、非有限数一律按 0 处理。 */
function pickNumber(row: Record<string, unknown>, key: string): number {
  const v = row[key];
  const n = typeof v === 'number' ? v : Number(v);
  return Number.isFinite(n) ? n : 0;
}

/**
 * 生成纯文本摘要（不含任何 HTML）：
 * 1. 先把所有空白（含换行）压成单个空格并 trim；
 * 2. 命中 needle 时取命中点前 40 字 ~ 后 40 字；
 * 3. 未命中（例如只有标题命中）则退化为正文前 80 字；
 * 4. 被截断的一侧用 '…' 标记。
 */
function buildSnippet(text: string, needle: string): string {
  const flat = text.replace(/\s+/g, ' ').trim();
  if (flat === '') return '';

  const target = needle.toLowerCase();
  const hitAt = target === '' ? -1 : flat.toLowerCase().indexOf(target);

  let start: number;
  let end: number;

  if (hitAt < 0) {
    start = 0;
    end = Math.min(flat.length, FALLBACK_CHARS);
  } else {
    start = Math.max(0, hitAt - CONTEXT_CHARS);
    end = Math.min(flat.length, hitAt + target.length + CONTEXT_CHARS);
  }

  const body = flat.slice(start, end).trim();
  const prefix = start > 0 ? '…' : '';
  const suffix = end < flat.length ? '…' : '';
  return `${prefix}${body}${suffix}`;
}

/** GET /api/search?q=关键词&limit=20 —— 跨 chapters / outlines / bible 的全局关键词搜索。 */
export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const query = (url.searchParams.get('q') ?? '').trim();

    if (query === '') {
      return NextResponse.json({ query: '', total: 0, items: [] });
    }

    const limit = normalizeLimit(url.searchParams.get('limit'));
    // 所有用户输入只进 ? 参数绑定，绝不拼进 SQL 文本。
    const pattern = `%${escapeLike(query)}%`;

    initDb();
    const db = getDb();

    // 注意：模板字符串里写 ESCAPE '\\'，生成的实际 SQL 是 ESCAPE '\'
    const chapterRows = db
      .prepare(
        `SELECT c.id AS id, c.title AS title, c.content AS content,
                b.id AS book_id, b.title AS book_title
         FROM chapters c
         JOIN books b ON b.id = c.book_id
         WHERE c.title LIKE ? ESCAPE '\\' OR c.content LIKE ? ESCAPE '\\'
         ORDER BY c.updated_at DESC, c.id DESC
         LIMIT ?`,
      )
      .all(pattern, pattern, limit) as unknown as Array<Record<string, unknown>>;

    const outlineRows = db
      .prepare(
        `SELECT o.id AS id, o.title AS title, o.summary AS content,
                b.id AS book_id, b.title AS book_title
         FROM outlines o
         JOIN books b ON b.id = o.book_id
         WHERE o.title LIKE ? ESCAPE '\\' OR o.summary LIKE ? ESCAPE '\\'
         ORDER BY o.seq DESC, o.id DESC
         LIMIT ?`,
      )
      .all(pattern, pattern, limit) as unknown as Array<Record<string, unknown>>;

    const bibleRows = db
      .prepare(
        `SELECT e.id AS id, e.title AS title, e.content AS content,
                b.id AS book_id, b.title AS book_title
         FROM bible e
         JOIN books b ON b.id = e.book_id
         WHERE e.title LIKE ? ESCAPE '\\' OR e.content LIKE ? ESCAPE '\\'
         ORDER BY e.id DESC
         LIMIT ?`,
      )
      .all(pattern, pattern, limit) as unknown as Array<Record<string, unknown>>;

    const toItems = (rows: Array<Record<string, unknown>>, type: SearchType): SearchItem[] =>
      rows.map((row) => ({
        bookId: Number(pickNumber(row, 'book_id')),
        bookTitle: String(pickString(row, 'book_title')),
        type,
        id: Number(pickNumber(row, 'id')),
        title: String(pickString(row, 'title')),
        snippet: buildSnippet(pickString(row, 'content'), query),
      }));

    // 合并顺序固定：chapter → outline → bible，同类内部保持各自 SQL 的倒序。
    const items: SearchItem[] = [
      ...toItems(chapterRows, 'chapter'),
      ...toItems(outlineRows, 'outline'),
      ...toItems(bibleRows, 'bible'),
    ].slice(0, limit);

    // 真实命中总数：三类各一条 COUNT(*)，条件与上面的 LIKE 完全一致（参数绑定相同），
    // 不受各查询自身 LIMIT 的影响。
    const countOf = (sql: string): number => {
      const row = db.prepare(sql).get(pattern, pattern) as unknown as
        | Record<string, unknown>
        | undefined;
      return row === undefined ? 0 : Number(pickNumber(row, 'n'));
    };

    const chapterTotal = countOf(
      `SELECT COUNT(*) AS n
       FROM chapters c
       JOIN books b ON b.id = c.book_id
       WHERE c.title LIKE ? ESCAPE '\\' OR c.content LIKE ? ESCAPE '\\'`,
    );
    const outlineTotal = countOf(
      `SELECT COUNT(*) AS n
       FROM outlines o
       JOIN books b ON b.id = o.book_id
       WHERE o.title LIKE ? ESCAPE '\\' OR o.summary LIKE ? ESCAPE '\\'`,
    );
    const bibleTotal = countOf(
      `SELECT COUNT(*) AS n
       FROM bible e
       JOIN books b ON b.id = e.book_id
       WHERE e.title LIKE ? ESCAPE '\\' OR e.content LIKE ? ESCAPE '\\'`,
    );
    const total = chapterTotal + outlineTotal + bibleTotal;

    return NextResponse.json({ query, total, items });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
