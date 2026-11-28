import { randomUUID } from 'node:crypto';
import { NextResponse } from 'next/server';
import { getDb, initDb } from '@/lib/db.js';
import { countWords } from '@/lib/wordcount.js';
import { deleteBible, getBible, listChapters, listOutlines, updateBible } from '@/lib/repo.js';
import { collectRenameChanges, normalizeBiblePatch } from '@/lib/bible.js';

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

/** 历史快照来源（与手动编辑 / 全书查找替换同口径）。 */
const REVISION_SOURCE = 'manual';

/** 未做替换时的稳定返回体。 */
const NO_REPLACEMENT = { chapters: 0, outlines: 0, occurrences: 0 };

/**
 * PATCH /api/bible/[id] —— 部分更新一条设定集条目（category / title / content 任意子集）。
 *
 * 可选字段 replaceInBook（布尔，缺省 false）：只有「本次传了 title」「新 title trim 后
 * 与原 title 不同」「replaceInBook === true」三项同时满足时，才把本书范围内
 * chapters.content / chapters.title / outlines.title / outlines.summary 里的旧名字
 * 字面量替换成新名字；否则只改设定本身。
 *
 * 原子性：设定更新 + 章节正文/标题替换 + 大纲标题/摘要替换 + 章节历史快照
 * 全部包在同一个 better-sqlite3 事务里，任一步失败整体回滚。
 */
export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bibleId = Number(id);
    if (Number.isNaN(bibleId)) {
      return NextResponse.json({ error: 'id 非法' }, { status: 400 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;

    // replaceInBook 只接受布尔值；其它类型直接 400，避免「'true' 字符串」这类隐式真值误触发全书替换。
    const hasReplaceFlag = Object.prototype.hasOwnProperty.call(body, 'replaceInBook');
    if (hasReplaceFlag && typeof body.replaceInBook !== 'boolean') {
      return NextResponse.json(
        { error: 'replaceInBook 必须是布尔值' },
        { status: 400 },
      );
    }
    const replaceInBook = body.replaceInBook === true;

    const { values, error } = normalizeBiblePatch(body);
    if (error !== null) {
      return NextResponse.json({ error }, { status: 400 });
    }

    const existing = getBible(bibleId);
    if (existing === undefined) {
      return NextResponse.json({ error: '设定不存在' }, { status: 404 });
    }

    const hasTitle = Object.prototype.hasOwnProperty.call(body, 'title');
    const nextTitle = hasTitle && typeof values.title === 'string' ? values.title : '';
    const oldTitle = typeof existing.title === 'string' ? existing.title : '';
    // 只有「传了 title + trim 后确实变了 + replaceInBook === true」才触发全书替换。
    const shouldReplace = hasTitle && nextTitle !== '' && nextTitle !== oldTitle.trim() && replaceInBook;

    let updated: Record<string, unknown> | null = null;
    let replaced = { ...NO_REPLACEMENT };

    if (!shouldReplace) {
      updated = updateBible(bibleId, values);
      if (updated === null) {
        return NextResponse.json({ error: '设定不存在' }, { status: 404 });
      }
      return NextResponse.json({ item: updated, replaced });
    }

    const bookId = Number(existing.bookId);
    const plan = collectRenameChanges(
      { chapters: listChapters(bookId), outlines: listOutlines(bookId) },
      oldTitle,
      nextTitle,
    );

    const db = getDb();
    const insertRevision = db.prepare(
      `INSERT INTO chapter_revisions (id, chapter_id, content, word_count, source, created_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))`,
    );
    const updateChapterContent = db.prepare(
      `UPDATE chapters
          SET content = ?, word_count = ?, updated_at = datetime('now')
        WHERE id = ?`,
    );
    const updateChapterTitle = db.prepare(
      `UPDATE chapters
          SET title = ?, updated_at = datetime('now')
        WHERE id = ?`,
    );
    const updateOutline = db.prepare(
      `UPDATE outlines
          SET title = ?, summary = ?
        WHERE id = ?`,
    );

    // 单一事务：设定自身 + 正文/标题 + 大纲 + 历史快照同生共死。
    const run = db.transaction(() => {
      const item = updateBible(bibleId, values);
      if (item === null) throw new Error('设定不存在');
      updated = item;

      for (const chapter of plan.chapters) {
        let touched = false;
        if (chapter.contentChanged) {
          // 正文被改动：先按「替换前正文」写一条历史快照（source='manual'）。
          // countWords 只统计正文，因此字数只随正文变化；仅改标题时字数不变。
          const oldWordCount = countWords(chapter.contentBefore);
          insertRevision.run(
            randomUUID(),
            chapter.id,
            chapter.contentBefore,
            oldWordCount,
            REVISION_SOURCE,
          );
          const newWordCount = countWords(chapter.contentAfter);
          const info = updateChapterContent.run(chapter.contentAfter, newWordCount, chapter.id);
          if (!info || info.changes !== 1) {
            throw new Error(`章节 ${chapter.id} 正文替换失败，已回滚本次设定改名`);
          }
          touched = true;
        }
        if (chapter.titleChanged) {
          const info = updateChapterTitle.run(chapter.titleAfter, chapter.id);
          if (!info || info.changes !== 1) {
            throw new Error(`章节 ${chapter.id} 标题替换失败，已回滚本次设定改名`);
          }
          touched = true;
        }
        if (!touched) continue;
      }

      for (const outline of plan.outlines) {
        const info = updateOutline.run(outline.titleAfter, outline.summaryAfter, outline.id);
        if (!info || info.changes !== 1) {
          throw new Error(`大纲 ${outline.id} 替换失败，已回滚本次设定改名`);
        }
      }
    });

    run();

    replaced = {
      chapters: plan.chapterCount,
      outlines: plan.outlineCount,
      occurrences: plan.occurrences,
    };

    return NextResponse.json({ item: updated, replaced });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
