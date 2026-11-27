import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getChapter, listBible, logLlm } from '@/lib/repo.js';
import { chat, isLlmConfigured, LlmError } from '@/lib/llm.js';
import { buildBibleExtractPrompt, parseBibleCandidates } from '@/lib/bible-extract.js';

/** 解析路由段的 id：必须是整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 取本书已有设定标题，供去重与 prompt 使用；查询失败时按空处理。 */
function existingBibleTitles(bookId: number): string[] {
  try {
    return listBible(bookId)
      .map((item) => (typeof item.title === 'string' ? item.title.trim() : ''))
      .filter((title) => title !== '');
  } catch {
    return [];
  }
}

/**
 * POST /api/chapters/[id]/extract-bible —— 从本章正文提取设定候选（不落库）。
 *
 * 无请求体；返回 { candidates: [{ category, title, content }], skippedDuplicates }。
 * 正文为空 / LLM 未配置 → 400；LLM 调用失败或输出不是合法 JSON → 502。
 */
export async function POST(_req: Request, { params }: { params: Promise<{ id: string }> }) {
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

    const content = typeof chapter.content === 'string' ? chapter.content : '';
    if (content.trim() === '') {
      return NextResponse.json({ error: '章节正文为空，无法提取设定' }, { status: 400 });
    }

    if (!isLlmConfigured()) {
      return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
    }

    const bookId = typeof chapter.bookId === 'number' ? chapter.bookId : null;
    const titles = bookId === null ? [] : existingBibleTitles(bookId);

    const title =
      typeof chapter.title === 'string' && chapter.title.trim() !== ''
        ? chapter.title.trim()
        : `第 ${chapterId} 章`;
    const { system, user } = buildBibleExtractPrompt({
      chapterTitle: title,
      content,
      existingTitles: titles,
    });

    const startedAt = Date.now();
    let raw = '';
    try {
      raw = await chat({
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: user },
        ],
        temperature: 0.2,
        maxTokens: 800,
      });
    } catch (err) {
      const message =
        err instanceof LlmError ? err.message : err instanceof Error ? err.message : String(err);
      return NextResponse.json({ error: message }, { status: 502 });
    }

    let result: { candidates: Array<{ category: string; title: string; content: string }>; skippedDuplicates: number };
    try {
      result = parseBibleCandidates(raw, titles);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return NextResponse.json({ error: message }, { status: 502 });
    }

    try {
      logLlm({
        bookId,
        kind: 'extract-bible',
        prompt: user,
        response: raw,
        elapsedMs: Date.now() - startedAt,
      });
    } catch {
      // 日志失败不影响候选返回。
    }

    return NextResponse.json({
      candidates: result.candidates,
      skippedDuplicates: result.skippedDuplicates,
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
