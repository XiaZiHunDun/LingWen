import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, listBible, listChapters, listOutlines, logLlm } from '@/lib/repo.js';
import { chatStream, isLlmConfigured, LlmError } from '@/lib/llm.js';

/** 设定集单条 category / title / content 注入 prompt 的最大长度（字符）。 */
const MAX_BIBLE_SNIPPET = 200;
/** 当前章节正文只取末尾多少字符。 */
const MAX_CHAPTER_TAIL = 800;
/** 最近参考章节数。 */
const MAX_RECENT_CHAPTERS = 3;
/** 大纲 / 章节摘要注入 prompt 的最大长度（字符）。 */
const MAX_SUMMARY = 200;

/** 解析路由段的 id：必须是整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 数值字段归一：非有限数一律返回 null。 */
function toNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

/** 字符串字段归一：非字符串一律返回空串，避免 prompt 里出现 [object Object]。 */
function toText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

/** 截断长文本，用于把设定 / 摘要塞进 prompt。 */
function clip(text: string, limit: number): string {
  const trimmed = text.trim();
  return trimmed.length > limit ? `${trimmed.slice(0, limit)}…` : trimmed;
}

/** 取文本末尾若干字符（用于「本章正文末尾」）。 */
function tail(text: string, limit: number): string {
  const trimmed = text.trim();
  return trimmed.length > limit ? trimmed.slice(-limit) : trimmed;
}

/**
 * POST /api/books/[id]/assist —— 针对某本书的写作助手问答（流式，non-UI）。
 *
 * body: { question: string, chapterId?: number }
 * 响应：text/plain 流式文本；流结束后写 llm_logs（kind = 'assist'）。
 */
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return NextResponse.json({ error: 'id 非法：必须是数字' }, { status: 400 });
    }

    const book = getBook(bookId);
    if (book === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
    const question = typeof body.question === 'string' ? body.question.trim() : '';
    if (question === '') {
      return NextResponse.json({ error: '问题不能为空' }, { status: 400 });
    }

    const rawChapterId = toNumber(body.chapterId);
    const requestedChapterId =
      rawChapterId !== null && Number.isInteger(rawChapterId) ? rawChapterId : null;

    if (!isLlmConfigured()) {
      return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
    }

    // ---- 收集上下文 ----
    const chapters: Array<Record<string, unknown>> = listChapters(bookId);
    const currentChapter =
      requestedChapterId === null
        ? undefined
        : chapters.find((item) => toNumber(item.id) === requestedChapterId);

    const bookLines: string[] = [];
    const title = toText(book.title);
    const genre = toText(book.genre);
    const summary = toText(book.summary);
    const style = toText(book.style);
    if (title !== '') bookLines.push(`书名：${title}`);
    if (genre !== '') bookLines.push(`类型：${genre}`);
    if (summary !== '') bookLines.push(`简介：${summary}`);
    if (style !== '') bookLines.push(`风格：${style}`);

    const bibleLines: string[] = listBible(bookId)
      .map((item) => {
        const category = clip(toText(item.category), MAX_BIBLE_SNIPPET);
        const itemTitle = clip(toText(item.title), MAX_BIBLE_SNIPPET);
        const content = clip(toText(item.content), MAX_BIBLE_SNIPPET);
        const head = [category, itemTitle].filter((part) => part !== '').join('·');
        if (head === '' && content === '') return '';
        return `- ${head === '' ? '设定' : head}：${content === '' ? '（无内容）' : content}`;
      })
      .filter((line) => line !== '');

    const outlineLines: string[] = listOutlines(bookId)
      .map((item) => {
        const seq = toNumber(item.seq);
        const itemTitle = clip(toText(item.title), MAX_SUMMARY);
        const itemSummary = clip(toText(item.summary), MAX_SUMMARY);
        const parts: string[] = [];
        if (seq !== null) parts.push(`第 ${seq} 章`);
        if (itemTitle !== '') parts.push(itemTitle);
        const head = parts.join(' ');
        if (head === '' && itemSummary === '') return '';
        return `- ${head === '' ? '（无标题）' : head}：${itemSummary === '' ? '（无摘要）' : itemSummary}`;
      })
      .filter((line) => line !== '');

    // 当前章节：标题 + 正文末尾 800 字。
    const chapterLines: string[] = [];
    if (currentChapter !== undefined) {
      const chapterTitle = toText(currentChapter.title).trim();
      if (chapterTitle !== '') chapterLines.push(`标题：${chapterTitle}`);
      const chapterContent = tail(toText(currentChapter.content), MAX_CHAPTER_TAIL);
      if (chapterContent !== '') {
        chapterLines.push(`正文末尾（最后 ${MAX_CHAPTER_TAIL} 字）：\n${chapterContent}`);
      }
    }

    // 最近 3 章（有当前章节时只看它之前的章节）：「第N章 标题：摘要」。
    const recentPool = chapters
      .filter((item) => {
        const itemId = toNumber(item.id);
        if (itemId === null) return false;
        if (requestedChapterId === null) return true;
        return itemId < requestedChapterId;
      })
      .sort((a, b) => (toNumber(a.id) ?? 0) - (toNumber(b.id) ?? 0));

    const recentLines = recentPool.slice(-MAX_RECENT_CHAPTERS).map((item) => {
      const seq = toNumber(item.seq);
      const itemTitle = clip(toText(item.title), MAX_SUMMARY) || '（无题）';
      const itemSummary = clip(toText(item.summary), MAX_SUMMARY) || '（无摘要）';
      return `- ${seq !== null ? `第${seq}章 ` : ''}${itemTitle}：${itemSummary}`;
    });

    const systemPrompt = [
      '你是小说创作助手。',
      '回答要求：',
      '1. 只基于下面给出的书籍设定、大纲与章节信息回答，不要编造未提供的设定。',
      '2. 建议要具体可执行：明确指出场景、冲突、人物动作。',
      '3. 使用简体中文，简洁分段，总长度不超过 400 字。',
    ].join('\n');

    const userLines: string[] = [];
    if (bookLines.length > 0) userLines.push(`【书籍信息】\n${bookLines.join('\n')}`);
    if (bibleLines.length > 0) userLines.push(`【设定集】\n${bibleLines.join('\n')}`);
    if (outlineLines.length > 0) userLines.push(`【大纲】\n${outlineLines.join('\n')}`);
    if (chapterLines.length > 0) userLines.push(`【当前章节】\n${chapterLines.join('\n')}`);
    if (recentLines.length > 0) {
      userLines.push(`【最近章节（摘要）】\n${recentLines.join('\n')}`);
    }
    userLines.push(`【问题】${question}`);
    const userPrompt = userLines.join('\n\n');

    // ---- 流式生成 ----
    const encoder = new TextEncoder();
    const startedAt = Date.now();
    let accumulated = '';

    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          for await (const delta of chatStream({
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: userPrompt },
            ],
            temperature: 0.7,
            maxTokens: 900,
          })) {
            if (delta === '') continue;
            accumulated += delta;
            controller.enqueue(encoder.encode(delta));
          }

          // 记日志：失败也吞掉，不影响已经发出的流。
          try {
            logLlm({
              bookId,
              kind: 'assist',
              prompt: question,
              response: accumulated,
              elapsedMs: Date.now() - startedAt,
            });
          } catch {
            // 日志失败一律忽略。
          }
        } catch (err) {
          const message =
            err instanceof LlmError
              ? err.message
              : err instanceof Error
                ? err.message
                : String(err);
          controller.enqueue(encoder.encode(`\n[中断] ${message}`));
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
