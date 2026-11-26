import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';
import { countWords } from '@/lib/wordcount.js';

/**
 * POST /api/books/import/json —— 从 JSON 快照导入一本书。
 *
 * 请求体即 GET /api/books/[id]/export/json 产出的快照：
 *   { version: 1, book: { title, genre, summary, style }, bible: [...], outlines: [...], chapters: [...] }
 *
 * 处理要点：
 *   1. 校验 version === 1、book.title 去空白后非空、chapters 是数组；bible/outlines 非数组按空数组。
 *   2. 事务内新建书（同名 title 追加「（导入）」后缀），再插 bible / outlines / chapters。
 *   3. 忽略快照旧 id：插 outlines 时记录 oldOutlineId → newOutlineId，插 chapters 时翻译 outlineId
 *      （映射不到存 NULL）；wordCount 优先快照值，缺失时用 countWords(content) 计算并写入 word_count。
 *   4. 全部 SQL 参数化，动态部分无列名拼接。
 */

/** 未知名 JSON 值的对象收窄。 */
type JsonObject = Record<string, unknown>;

/** 同名书追加的后缀。 */
const DUPLICATE_SUFFIX = '（导入）';

/** 请求体对象收窄：非对象（含数组、null）返回 null。 */
function asObject(value: unknown): JsonObject | null {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return null;
  return value as JsonObject;
}

/** 可空字符串字段：非字符串一律 null。 */
function nullableString(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** 可空有限数字：支持 number 与数字字符串；其余返回 null。 */
function nullableNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

/** 可空整数字段（seq 等）：非整数部分截断；无法解析返回 null。 */
function nullableInteger(value: unknown): number | null {
  const parsed = nullableNumber(value);
  return parsed === null ? null : Math.trunc(parsed);
}

/** 数字 id 的字符串化键（用于新旧 outline id 映射）。 */
function idKey(value: unknown): string | null {
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value === 'string' && value.trim() !== '') return value.trim();
  return null;
}

/** 统一 400 返回。 */
function badRequest(message: string) {
  return NextResponse.json({ error: message }, { status: 400 });
}

export async function POST(req: Request) {
  try {
    initDb();

    let raw: unknown;
    try {
      raw = await req.json();
    } catch {
      return badRequest('请求体必须是合法 JSON');
    }

    const body = asObject(raw);
    if (body === null) {
      return badRequest('请求体必须是 JSON 对象');
    }

    if (body.version !== 1) {
      return badRequest('version 必须为 1');
    }

    // book 必须是对象、且 book.title 去空白后非空；两种情况统一返回同一提示。
    const bookInput = asObject(body.book);
    const rawTitle = bookInput === null ? undefined : bookInput.title;
    if (bookInput === null || typeof rawTitle !== 'string' || rawTitle.trim() === '') {
      return badRequest('book.title 不能为空');
    }

    if (!Array.isArray(body.chapters)) {
      return badRequest('chapters 必须是数组');
    }

    const title = rawTitle.trim();
    const genre = nullableString(bookInput.genre);
    const summary = nullableString(bookInput.summary);
    const style = nullableString(bookInput.style);

    const bibleItems: unknown[] = Array.isArray(body.bible) ? body.bible : [];
    const outlineItems: unknown[] = Array.isArray(body.outlines) ? body.outlines : [];
    const chapterItems: unknown[] = body.chapters;

    const db = getDb();
    const countTitle = db.prepare('SELECT COUNT(*) AS n FROM books WHERE title = ?');
    const insertBook = db.prepare(
      `INSERT INTO books (title, genre, summary, style, created_at, updated_at)
       VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))`,
    );
    const insertBible = db.prepare(
      'INSERT INTO bible (book_id, category, title, content) VALUES (?, ?, ?, ?)',
    );
    const insertOutline = db.prepare(
      'INSERT INTO outlines (book_id, seq, title, summary, status) VALUES (?, ?, ?, ?, ?)',
    );
    // 直接 prepared INSERT：保证 word_count 按快照值 / countWords 精确落库。
    const insertChapter = db.prepare(
      `INSERT INTO chapters
         (book_id, outline_id, seq, title, content, word_count, summary, status,
          created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))`,
    );

    const runImport = db.transaction(() => {
      // 1) 新建书：同名时追加「（导入）」后缀。
      const existing = countTitle.get(title) as { n?: unknown } | undefined;
      const duplicate = existing !== undefined && Number(existing.n ?? 0) > 0;
      const finalTitle = duplicate ? `${title}${DUPLICATE_SUFFIX}` : title;

      const bookInfo = insertBook.run(finalTitle, genre, summary, style);
      const newBookId = Number(bookInfo.lastInsertRowid);

      // 2) 设定集条目。
      for (const item of bibleItems) {
        const row = asObject(item);
        if (row === null) continue;
        insertBible.run(
          newBookId,
          nullableString(row.category),
          nullableString(row.title),
          nullableString(row.content),
        );
      }

      // 3) 大纲：建立 oldOutlineId → newOutlineId 映射。
      const outlineIdMap = new Map<string, number>();
      for (const item of outlineItems) {
        const row = asObject(item);
        if (row === null) continue;
        const info = insertOutline.run(
          newBookId,
          nullableInteger(row.seq),
          nullableString(row.title),
          nullableString(row.summary),
          nullableString(row.status),
        );
        const oldKey = idKey(row.id);
        if (oldKey !== null) outlineIdMap.set(oldKey, Number(info.lastInsertRowid));
      }

      // 4) 章节：翻译 outlineId，wordCount 缺失时按正文计算。
      for (const item of chapterItems) {
        const row = asObject(item);
        if (row === null) continue;
        const content = nullableString(row.content);
        const snapshotWords = nullableNumber(row.wordCount);
        const wordCount =
          snapshotWords === null
            ? countWords(content ?? '')
            : Math.max(0, Math.round(snapshotWords));

        const oldOutlineKey = idKey(row.outlineId);
        const outlineId =
          oldOutlineKey === null ? null : (outlineIdMap.get(oldOutlineKey) ?? null);

        insertChapter.run(
          newBookId,
          outlineId,
          nullableInteger(row.seq),
          nullableString(row.title),
          content,
          wordCount,
          nullableString(row.summary),
          nullableString(row.status),
        );
      }

      return newBookId;
    });

    const newId = runImport();
    return NextResponse.json({ id: newId }, { status: 201 });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
