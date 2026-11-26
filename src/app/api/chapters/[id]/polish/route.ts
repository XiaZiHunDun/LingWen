import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, getChapter, listBible, listOutlines, logLlm } from '@/lib/repo.js';
import { chatStream, isLlmConfigured, LlmError } from '@/lib/llm.js';

/** 书籍设定（书名 / 类型 / 风格 / 简介 / 设定集）注入 prompt 的最大长度（字符）。 */
const MAX_BOOK_SETTINGS = 2000;
/** 本章大纲注入 prompt 的最大长度（字符）。 */
const MAX_OUTLINE_SUMMARY = 600;
/** 单条设定注入 prompt 的最大长度（字符）。 */
const MAX_BIBLE_LINE = 200;
/** 额外要求注入 prompt 的最大长度（字符）。 */
const MAX_INSTRUCTION = 800;
/** 最多参考多少条设定。 */
const MAX_BIBLE_ITEMS = 20;
/** 输出 token 上限。 */
const MAX_TOKENS = 8000;

type PolishMode = 'polish' | 'condense' | 'expand';

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

/** mode 归一：非法值退回 polish。 */
function parseMode(value: unknown): PolishMode {
  if (value === 'condense' || value === 'expand' || value === 'polish') return value;
  return 'polish';
}

/** 每种模式对应的任务描述。 */
function taskLine(mode: PolishMode): string {
  switch (mode) {
    case 'condense':
      return '【任务】在保留全部关键情节、人物动作与对话功能的前提下，精简本章正文，删掉冗余表达与重复铺陈，使篇幅明显缩短、节奏更紧凑。';
    case 'expand':
      return '【任务】在保持原有情节走向、人物与设定不变的前提下，扩写本章正文，补充细节描写、心理活动、环境与动作描写，使内容更饱满。';
    default:
      return '【任务】润色本章正文：优化措辞、句式与节奏，修正错别字与病句，统一叙事人称与语气，情节、人物、设定一律不得改动。';
  }
}

/** 由正文长度估算 maxTokens：扩写需要更大余量。 */
function estimateMaxTokens(mode: PolishMode, contentLength: number): number {
  const factor = mode === 'expand' ? 2 : mode === 'condense' ? 1 : 1.4;
  return Math.max(1500, Math.min(MAX_TOKENS, Math.round(contentLength * factor) + 500));
}

/**
 * POST /api/chapters/[id]/polish —— 流式润色 / 精简 / 扩写章节正文（仅预览，不落库）。
 *
 * body: { mode?: 'polish' | 'condense' | 'expand', instruction?: string }
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

    if (!isLlmConfigured()) {
      return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
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
      if (summary !== '') outlineParts.push(`摘要：${clip(summary, MAX_OUTLINE_SUMMARY)}`);
    }

    // ---- 书籍设定摘要：整体截断到 MAX_BOOK_SETTINGS ----
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
    const bookSettings = clip(settingParts.join('\n'), MAX_BOOK_SETTINGS);

    // ---- 组装 prompt ----
    const systemPrompt = [
      '你是一位资深中文小说编辑，负责在保持原意的前提下修改章节正文。',
      '硬性要求：',
      '1. 只输出修改后的完整正文，一次输出全文，不要分段截断。',
      '2. 不要输出任何解释、说明、点评、建议或改动清单。',
      '3. 不要使用 Markdown：不要 ``` 代码块围栏、不要 #、不要列表符号、不要加粗。',
      '4. 不要输出章节标题行或章节号，直接输出正文。',
      '5. 不要输出「以下是修改后的正文」这类前言或收尾语。',
      '6. 使用简体中文，段落之间空一行。',
    ].join('\n');

    const userLines: string[] = [];
    if (bookSettings !== '') userLines.push(`【书籍设定】\n${bookSettings}`);
    if (outlineParts.length > 0) userLines.push(`【本章大纲】\n${outlineParts.join('\n')}`);
    userLines.push(`【本章标题】${chapterTitle}`);
    userLines.push(`【原文正文】\n${content}`);
    userLines.push(taskLine(mode));
    if (instruction !== '') {
      userLines.push(`【额外要求】${clip(instruction, MAX_INSTRUCTION)}`);
    }
    userLines.push('请直接输出修改后的完整正文。');
    const userPrompt = userLines.join('\n\n');

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
            temperature: mode === 'condense' ? 0.6 : 0.8,
            maxTokens: estimateMaxTokens(mode, content.length),
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
                prompt: userPrompt,
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
