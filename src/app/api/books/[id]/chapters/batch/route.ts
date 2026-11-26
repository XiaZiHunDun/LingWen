import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';
import {
  createChapter,
  getBook,
  getChapter,
  listChapters,
  recordWritingDelta,
} from '@/lib/repo.js';
import { countWords } from '@/lib/wordcount.js';

/** 单次批量操作允许的最大条目数（防止误传超大数组拖垮请求）。 */
const MAX_BATCH_SIZE = 200;

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/**
 * 校验并去重 id 数组。
 * 规则：非数组、或含「非正整数」元素 → 返回 null（调用方回 400）；
 * 空数组 → 返回空数组（由调用方按「0 条操作」成功返回，不算错误）。
 * 去重后保持首次出现的顺序。
 */
function parseIdList(value: unknown): number[] | null {
  if (!Array.isArray(value)) return null;
  const seen = new Set<number>();
  const ids: number[] = [];
  for (const item of value) {
    if (typeof item !== 'number' || !Number.isInteger(item) || item <= 0) return null;
    if (seen.has(item)) continue;
    seen.add(item);
    ids.push(item);
  }
  return ids;
}

/** 从行里取有限数字字段（兼容 camelCase 与 snake_case），否则 null。 */
function numberField(row: Record<string, unknown> | undefined, ...keys: string[]): number | null {
  if (row === undefined) return null;
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'number' && Number.isFinite(value)) return value;
  }
  return null;
}

/** 从行里取字符串字段（兼容 undefined），否则 null。 */
function stringField(row: Record<string, unknown> | undefined, ...keys: string[]): string | null {
  if (row === undefined) return null;
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'string') return value;
  }
  return null;
}

/** 取已有章节里最大的 seq（没有则 0），用于批量建章时递增编号。 */
function maxSeq(rows: Array<Record<string, unknown>>): number {
  let max = 0;
  for (const row of rows) {
    const seq = row.seq;
    if (typeof seq === 'number' && Number.isFinite(seq) && seq > max) {
      max = Math.floor(seq);
    }
  }
  return max;
}

/**
 * POST /api/books/[id]/chapters/batch —— 章节批量操作。
 * body: { action: 'delete', chapterIds: number[] }
 *    → 逐条删除该书下的章节（口径与单章 DELETE 一致：按正文字数记负增量）。
 *    → 返回 { deleted, skipped }
 * body: { action: 'create-from-outline', outlineIds: number[] }
 *    → 按大纲条目批量建章（该书已有同 outlineId 章节的大纲会被跳过，避免重复建章）。
 *    → 返回 { created, skipped, chapterIds }
 */
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }
    if (getBook(bookId) === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
    const action = body.action;
    if (action !== 'delete' && action !== 'create-from-outline') {
      return NextResponse.json(
        { error: "action 非法：仅支持 'delete' / 'create-from-outline'" },
        { status: 400 },
      );
    }

    // ------------------------------------------------------------------ *
    // action = 'delete'：批量删除章节
    // ------------------------------------------------------------------ *
    if (action === 'delete') {
      const chapterIds = parseIdList(body.chapterIds);
      if (chapterIds === null) {
        return NextResponse.json(
          { error: 'chapterIds 非法：必须是正整数数组' },
          { status: 400 },
        );
      }
      if (chapterIds.length > MAX_BATCH_SIZE) {
        return NextResponse.json(
          { error: `chapterIds 过多：单次最多 ${MAX_BATCH_SIZE} 条` },
          { status: 400 },
        );
      }
      if (chapterIds.length === 0) {
        return NextResponse.json({ deleted: 0, skipped: 0 });
      }

      const db = getDb();
      // 整批放在同一个事务里：删除 + 写作日历负增量要么全成，要么全不成。
      const removeOne = db.transaction((chapterId: number): boolean => {
        const chapter = getChapter(chapterId) as Record<string, unknown> | undefined;
        // 不存在、或不属于路径里的这本书 → 跳过（不报错，只计数）。
        if (chapter === undefined) return false;
        if (numberField(chapter, 'bookId', 'book_id') !== bookId) return false;
        // 写作日历：口径与单章 DELETE 一致，按现有正文字数记一次负增量。
        const removedWords = countWords(stringField(chapter, 'content') ?? '');
        if (removedWords !== 0) {
          recordWritingDelta({ bookId, chapterId, deltaWords: -removedWords });
        }
        db.prepare('DELETE FROM chapters WHERE id = ?').run(chapterId);
        return true;
      });

      let deleted = 0;
      for (const chapterId of chapterIds) {
        if (removeOne(chapterId)) deleted += 1;
      }
      return NextResponse.json({ deleted, skipped: chapterIds.length - deleted });
    }

    // ------------------------------------------------------------------ *
    // action = 'create-from-outline'：按大纲批量建章
    // ------------------------------------------------------------------ *
    const outlineIds = parseIdList(body.outlineIds);
    if (outlineIds === null) {
      return NextResponse.json(
        { error: 'outlineIds 非法：必须是正整数数组' },
        { status: 400 },
      );
    }
    if (outlineIds.length > MAX_BATCH_SIZE) {
      return NextResponse.json(
        { error: `outlineIds 过多：单次最多 ${MAX_BATCH_SIZE} 条` },
        { status: 400 },
      );
    }
    if (outlineIds.length === 0) {
      return NextResponse.json({ created: 0, skipped: 0, chapterIds: [] });
    }

    const db = getDb();
    const existing = listChapters(bookId) as Array<Record<string, unknown>>;
    let seqCursor = maxSeq(existing);
    // 已有章节引用的 outlineId 集合：这些大纲不再重复建章。
    const builtOutlineIds = new Set<number>();
    for (const row of existing) {
      const outlineId = numberField(row, 'outlineId', 'outline_id');
      if (outlineId !== null) builtOutlineIds.add(outlineId);
    }

    const createdChapterIds: number[] = [];
    let skipped = 0;
    const createOne = db.transaction((outlineId: number): number | null => {
      const outline = db.prepare('SELECT * FROM outlines WHERE id = ?').get(outlineId) as
        | Record<string, unknown>
        | undefined;
      if (outline === undefined) return null;
      if (numberField(outline, 'book_id', 'bookId') !== bookId) return null;
      if (builtOutlineIds.has(outlineId)) return null;
      seqCursor += 1;
      // 正文初始为空串，wordCount 由表格默认 0 兜底（countWords('') === 0）。
      const created = createChapter({
        bookId,
        outlineId,
        seq: seqCursor,
        title: stringField(outline, 'title'),
        content: '',
        summary: stringField(outline, 'summary'),
        status: stringField(outline, 'status'),
      }) as Record<string, unknown> | undefined;
      if (created === undefined) {
        seqCursor -= 1;
        return null;
      }
      builtOutlineIds.add(outlineId);
      return numberField(created, 'id');
    });

    for (const outlineId of outlineIds) {
      const newId = createOne(outlineId);
      if (newId === null) {
        skipped += 1;
        continue;
      }
      createdChapterIds.push(newId);
    }

    return NextResponse.json({
      created: createdChapterIds.length,
      skipped,
      chapterIds: createdChapterIds,
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
