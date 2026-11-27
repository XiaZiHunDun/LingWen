import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, getChapter, listBible, listChapters, listOutlines } from '@/lib/repo.js';
import { selectChapterContext } from '@/lib/chapter-context.js';

/** 解析路由段的 id：必须是整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/**
 * GET /api/chapters/[id]/context —— 预览本章生成时会注入的上下文。
 *
 * query：targetWords / mode / instruction（均可选，与 generate 请求体同义）。
 * 返回 { blocks: [{ key, label, chars }], totalChars, promptText, stats }。
 * 只读：不写库、不调 LLM，上下文完全由 selectChapterContext 组装，保证「预览 = 实际注入」。
 */
export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const chapterId = parseId(id);
    if (chapterId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }

    const chapter = getChapter(chapterId);
    if (chapter === undefined) {
      return NextResponse.json({ error: '章节不存在' }, { status: 404 });
    }

    const bookId = typeof chapter.bookId === 'number' ? chapter.bookId : null;
    const book = bookId === null ? undefined : getBook(bookId);
    const bible = bookId === null ? [] : listBible(bookId);
    const chapters = bookId === null ? [] : listChapters(bookId);
    const outlines = bookId === null ? [] : listOutlines(bookId);

    const url = new URL(req.url);
    const rawWords = url.searchParams.get('targetWords');
    const parsedWords = rawWords === null ? Number.NaN : Number(rawWords);
    const targetWords = Number.isFinite(parsedWords) ? parsedWords : undefined;
    const rawMode = url.searchParams.get('mode');
    const mode = rawMode === 'replace' ? 'replace' : rawMode === 'append' ? 'append' : undefined;
    const instruction = url.searchParams.get('instruction') ?? '';

    const context = selectChapterContext({
      book,
      bible,
      outlines,
      chapters,
      currentChapter: chapter,
      existingContent: typeof chapter.content === 'string' ? chapter.content : '',
      targetWords,
      mode,
      instruction,
    });

    return NextResponse.json({
      blocks: context.blocks.map((block) => ({
        key: block.key,
        label: block.label,
        chars: block.chars,
      })),
      totalChars: context.totalChars,
      promptText: context.promptText,
      stats: context.stats,
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
