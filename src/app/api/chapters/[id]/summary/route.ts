import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getChapter, logLlm, updateChapter } from '@/lib/repo.js';
import { chat, isLlmConfigured, LlmError } from '@/lib/llm.js';
import {
  SUMMARY_MAX_CHARS,
  SUMMARY_MAX_TOKENS,
  buildChapterSummaryPrompt,
  clipSummary,
} from '@/lib/chapter-summary.js';

/** 解析路由段的 id：必须是整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/**
 * POST /api/chapters/[id]/summary —— 为本章正文生成 ≤200 字摘要并覆盖旧值。
 *
 * 无请求体；返回 { summary, chars }。
 * 正文为空 / LLM 未配置 → 400；LLM 调用失败 → 502。
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
      return NextResponse.json({ error: '章节正文为空，无法生成摘要' }, { status: 400 });
    }

    if (!isLlmConfigured()) {
      return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
    }

    const title =
      typeof chapter.title === 'string' && chapter.title.trim() !== ''
        ? chapter.title.trim()
        : `第 ${chapterId} 章`;
    const { system, user } = buildChapterSummaryPrompt({
      title,
      content,
      maxChars: SUMMARY_MAX_CHARS,
    });

    const startedAt = Date.now();
    let raw = '';
    try {
      raw = await chat({
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: user },
        ],
        temperature: 0.3,
        maxTokens: SUMMARY_MAX_TOKENS,
      });
    } catch (err) {
      const message =
        err instanceof LlmError ? err.message : err instanceof Error ? err.message : String(err);
      return NextResponse.json({ error: message }, { status: 502 });
    }

    const summary = clipSummary(raw, SUMMARY_MAX_CHARS);
    if (summary === '') {
      return NextResponse.json({ error: 'LLM 未返回可用摘要' }, { status: 502 });
    }

    updateChapter(chapterId, { summary });

    try {
      logLlm({
        bookId: typeof chapter.bookId === 'number' ? chapter.bookId : null,
        kind: 'summary',
        prompt: user,
        response: raw,
        elapsedMs: Date.now() - startedAt,
      });
    } catch {
      // 日志失败不影响摘要落库结果。
    }

    return NextResponse.json({ summary, chars: summary.length });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
