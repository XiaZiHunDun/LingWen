import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, getChapter, listBible, listOutlines, logLlm } from '@/lib/repo.js';
import { chatStream, isLlmConfigured, LlmError } from '@/lib/llm.js';
import { buildPolishPrompt, normalizePolishSelection, PolishSelectionError } from '@/lib/polish-prompt.js';

/** 单条设定注入 prompt 的最大长度（字符）。 */
const MAX_BIBLE_LINE = 200;
/** 最多参考多少条设定。 */
const MAX_BIBLE_ITEMS = 20;

/** 解析路由段的 id：必须是整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 字符串字段归一：非字符串一律返回空串。 */
function toText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

/** 数值字段归一：非有限数一律返回 null。 */
function toNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

/** 截断长文本。 */
function clip(text: string, limit: number): string {
  const trimmed = text.trim();
  return trimmed.length > limit ? `${trimmed.slice(0, limit)}…` : trimmed;
}

/**
 * POST /api/chapters/[id]/polish —— 流式润色 / 精简 / 扩写章节正文（仅预览，不落库）。
 *
 * body: { mode?: 'polish' | 'condense' | 'expand', instruction?: string,
 *         selection?: string, before?: string, after?: string }
 * - selection trim 后非空 → 片段模式：只改写选中片段，输出只有改写后的片段本身。
 * - selection 为空 → 整章模式（原有行为）。
 * 响应：text/plain 流式正文；结束后只写 llm_logs（kind='polish'），不改动 chapters 表正文。
 */
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
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

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;

    // 选区参数归一（trim / 超长 400 / before·after 截断到 500）——先于 LLM 配置校验，
    // 保证参数问题总能拿到 400 与明确文案。
    let selectionInfo: ReturnType<typeof normalizePolishSelection>;
    try {
      selectionInfo = normalizePolishSelection({
        selection: body.selection,
        before: body.before,
        after: body.after,
      });
    } catch (err) {
      if (err instanceof PolishSelectionError) {
        return NextResponse.json({ error: err.message }, { status: 400 });
      }
      throw err;
    }

    if (!isLlmConfigured()) {
      return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
    }

    const mode = parseMode(body.mode);
    const instruction = typeof body.instruction === 'string' ? body.instruction.trim() : '';

    const content = toText(chapter.content);
    if (content.trim() === '') {
      return NextResponse.json({ error: '本章正文为空，无法润色' }, { status: 400 });
    }

    const chapterTitle = toText(chapter.title) || `第 ${chapterId} 章`;
    const bookId = toNumber(chapter.bookId);
    const book = bookId === null ? undefined : getBook(bookId);
    const bible = bookId === null ? [] : listBible(bookId);
    const outlineRows: Array<Record<string, unknown>> =
      bookId === null ? [] : listOutlines(bookId);

    // ---- 本章大纲（若有）----
    const outlineId = toNumber(chapter.outlineId);
    const matchedOutline =
      outlineId === null ? undefined : outlineRows.find((item) => toNumber(item.id) === outlineId);
    const outlineParts: string[] = [];
    if (matchedOutline !== undefined) {
      const title = toText(matchedOutline.title);
      const summary = toText(matchedOutline.summary);
      if (title !== '') outlineParts.push(`标题：${title}`);
      if (summary !== '') outlineParts.push(`摘要：${clip(summary, 600)}`);
    }

    // ---- 书籍设定块（长度上限由 polish-prompt 统一处理）----
    const settingParts: string[] = [];
    if (book !== undefined) {
      const title = toText(book.title);
      const genre = toText(book.genre);
      const style = toText(book.style);
      const summary = toText(book.summary);
      if (title) settingParts.push(`书名：${title}`);
      if (genre) settingParts.push(`类型：${genre}`);
      if (style) settingParts.push(`风格：${style}`);
      if (summary) settingParts.push(`全书简介：${summary}`);
    }
    const bibleLines = bible
      .map((item) => {
        const category = toText(item.category);
        const title = toText(item.title);
        const text = toText(item.content);
        const head = [category, title].filter((part) => part !== '').join('·');
        if (head === '' && text === '') return '';
        return `- ${head === '' ? '设定' : head}：${clip(text, MAX_BIBLE_LINE)}`;
      })
      .filter((line) => line !== '')
      .slice(0, MAX_BIBLE_ITEMS);
    if (bibleLines.length > 0) settingParts.push(`设定集：\n${bibleLines.join('\n')}`);

    // ---- prompt 组装全部交给 polish-prompt ----
    const prompt = buildPolishPrompt({
      mode,
      chapterTitle,
      bookSettings: settingParts.join('\n'),
      outline: outlineParts.join('\n'),
      content,
      instruction,
      selection: selectionInfo.selection,
      before: selectionInfo.before,
      after: selectionInfo.after,
    });

    const encoder = new TextEncoder();
    const startedAt = Date.now();
    let accumulated = '';

    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          for await (const delta of chatStream({
            messages: [
              { role: 'system', content: prompt.system },
              { role: 'user', content: prompt.user },
            ],
            temperature: mode === 'condense' ? 0.6 : 0.8,
            maxTokens: prompt.maxTokens,
          })) {
            if (delta === '') continue;
            accumulated += delta;
            controller.enqueue(encoder.encode(delta));
          }

          // 只记日志，不落库：正文由前端「应用」时走 PATCH 保存。
          try {
            if (accumulated.trim() !== '') {
              logLlm({
                bookId,
                kind: 'polish',
                prompt: prompt.user,
                response: accumulated,
                elapsedMs: Date.now() - startedAt,
              });
            }
          } catch {
            // 日志失败不影响已发出的流。
          }
        } catch (err) {
          const message =
            err instanceof LlmError
              ? err.message
              : err instanceof Error
                ? err.message
                : String(err);
          controller.enqueue(encoder.encode(`\n[润色中断] ${message}`));
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

/** mode 归一：非法值退回 polish。 */
function parseMode(value: unknown): 'polish' | 'condense' | 'expand' {
  if (value === 'condense' || value === 'expand' || value === 'polish') return value;
  return 'polish';
}
