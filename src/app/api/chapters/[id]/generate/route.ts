import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import {
  createChapterRevision,
  getBook,
  getChapter,
  listBible,
  listChapters,
  listOutlines,
  logLlm,
  pruneChapterRevisions,
  updateChapter,
} from '@/lib/repo.js';
import { countWords } from '@/lib/wordcount.js';
import { chatStream, isLlmConfigured, LlmError } from '@/lib/llm.js';

/** 默认目标字数。 */
const DEFAULT_TARGET_WORDS = 1200;
/** 目标字数下限 / 上限。 */
const MIN_TARGET_WORDS = 300;
const MAX_TARGET_WORDS = 4000;
/** 前文最多参考多少章。 */
const MAX_PREVIOUS_CHAPTERS = 3;
/** 单条设定 / 摘要注入 prompt 的最大长度（字符）。 */
const MAX_SNIPPET = 300;
/** 本章大纲摘要注入 prompt 的最大长度（字符）。 */
const MAX_OUTLINE_SUMMARY = 300;
/** 本章已有正文回灌 prompt 时只取末尾多少字符（用于衔接上文）。 */
const MAX_EXISTING_CONTENT = 600;
/** 每个章节保留的历史版本条数。 */
const KEEP_REVISIONS = 20;

type Mode = 'append' | 'replace';

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
function clip(text: string, limit: number = MAX_SNIPPET): string {
  const trimmed = text.trim();
  return trimmed.length > limit ? `${trimmed.slice(0, limit)}…` : trimmed;
}

/** 目标字数 clamp 到 [MIN, MAX]，非法值按默认值处理。 */
function clampTargetWords(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return DEFAULT_TARGET_WORDS;
  const rounded = Math.round(value);
  return Math.min(MAX_TARGET_WORDS, Math.max(MIN_TARGET_WORDS, rounded));
}

/** 由目标字数估算 maxTokens：中文约 1 字 ≈ 1 token，留足余量且不低于 1500。 */
function estimateMaxTokens(targetWords: number): number {
  return Math.max(1500, Math.min(8000, Math.round(targetWords * 1.6)));
}

/** 挑出当前章节之前（id 更小）的最近 N 章，只保留 title + summary。 */
function pickPreviousChapters(
  chapters: Array<Record<string, unknown>>,
  currentId: number,
): Array<{ title: string; summary: string }> {
  return chapters
    .filter((item) => {
      const itemId = toNumber(item.id);
      return itemId !== null && itemId < currentId;
    })
    .sort((a, b) => (toNumber(b.id) ?? 0) - (toNumber(a.id) ?? 0))
    .slice(0, MAX_PREVIOUS_CHAPTERS)
    .reverse()
    .map((item) => ({ title: toText(item.title), summary: toText(item.summary) }));
}

/**
 * 按 outlineId 在本书大纲里找对应条目；找不到返回 undefined。
 * 只取 title / summary 两项，summary 由调用方截断。
 */
function pickChapterOutline(
  outlines: Array<Record<string, unknown>>,
  outlineId: number | null,
): { title: string; summary: string } | undefined {
  if (outlineId === null) return undefined;
  const matched = outlines.find((item) => toNumber(item.id) === outlineId);
  if (matched === undefined) return undefined;
  return { title: toText(matched.title), summary: toText(matched.summary) };
}

/**
 * POST /api/chapters/[id]/generate —— 流式续写 / 重写章节正文。
 *
 * body: { instruction?: string, targetWords?: number, mode?: 'append' | 'replace' }
 * 响应：text/plain 流式正文；流结束后落库（content / wordCount / status）并写 llm_logs。
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
    const instruction = typeof body.instruction === 'string' ? body.instruction.trim() : '';
    const programTargetWords = clampTargetWords(body.targetWords);
    const mode: Mode = body.mode === 'replace' ? 'replace' : 'append';

    const bookId = toNumber(chapter.bookId);
    const book = bookId === null ? undefined : getBook(bookId);
    const bible = bookId === null ? [] : listBible(bookId);
    const previous = bookId === null ? [] : pickPreviousChapters(listChapters(bookId), chapterId);
    const outlineRows: Array<Record<string, unknown>> =
      bookId === null ? [] : listOutlines(bookId);
    const outline = pickChapterOutline(outlineRows, toNumber(chapter.outlineId));

    const existingContent = toText(chapter.content);
    const chapterTitle = toText(chapter.title) || `第 ${chapterId} 章`;

    // ---- 组装 prompt ----
    const bookLines: string[] = [];
    if (book !== undefined) {
      const title = toText(book.title);
      const genre = toText(book.genre);
      const style = toText(book.style);
      const summary = toText(book.summary);
      if (title) bookLines.push(`书名：${title}`);
      if (genre) bookLines.push(`类型：${genre}`);
      if (style) bookLines.push(`风格：${style}`);
      if (summary) bookLines.push(`全书简介：${clip(summary)}`);
    }

    const bibleLines = bible
      .map((item) => {
        const category = toText(item.category);
        const title = toText(item.title);
        const content = toText(item.content);
        const head = [category, title].filter((part) => part !== '').join('·');
        if (head === '' && content === '') return '';
        return `- ${head === '' ? '设定' : head}：${clip(content)}`;
      })
      .filter((line) => line !== '');

    const previousLines = previous
      .map((item) => `- ${item.title || '（无题）'}：${clip(item.summary) || '（无摘要）'}`)
      .filter((line) => line !== '');

    // 本章大纲：title / summary 来自 outlines 表，summary 最多 300 字。
    const outlineLines: string[] = [];
    if (outline !== undefined) {
      if (outline.title !== '') outlineLines.push(`标题：${outline.title}`);
      const outlineSummary = clip(outline.summary, MAX_OUTLINE_SUMMARY);
      if (outlineSummary !== '') outlineLines.push(`摘要：${outlineSummary}`);
    }

    const systemPrompt = [
      '你是一位中文小说作家，负责续写或重写章节正文。',
      '硬性要求：',
      '1. 只输出小说正文，使用简体中文。',
      '2. 不要输出标题行、章节号或任何形式的题目。',
      '3. 不要解释、不要说明、不要点评、不要写「以上」之类的收尾语。',
      '4. 不要使用 Markdown：不要 ``` 围栏、不要 #、不要列表符号、不要加粗。',
      '5. 延续已有前文的叙事风格、人物设定与世界观，保持前后一致。',
      '6. 用自然段分隔，段与段之间空一行。',
    ].join('\n');

    const userLines: string[] = [];
    if (bookLines.length > 0) userLines.push(`【书籍信息】\n${bookLines.join('\n')}`);
    if (bibleLines.length > 0) {
      userLines.push(`【设定集】\n${bibleLines.slice(0, 20).join('\n')}`);
    }
    if (previousLines.length > 0) {
      userLines.push(`【前情提要（更早章节，仅摘要）】\n${previousLines.join('\n')}`);
    }
    if (outlineLines.length > 0) {
      userLines.push(`【本章大纲】\n${outlineLines.join('\n')}`);
      userLines.push('【大纲要求】本章情节须围绕上面的大纲展开，不要偏移主线。');
    }
    userLines.push(`【本章标题】${chapterTitle}`);
    if (existingContent.trim() !== '') {
      // 只取末尾 600 字，明确标注用途是「衔接上文」，避免模型整段复述。
      const tail =
        existingContent.length > MAX_EXISTING_CONTENT
          ? existingContent.slice(-MAX_EXISTING_CONTENT)
          : existingContent;
      userLines.push(
        `【衔接上文（本章已有正文的最后 ${MAX_EXISTING_CONTENT} 字，仅用于保持语气、人物与情节衔接，不要照抄这些句子）】\n${tail}`,
      );
    }
    userLines.push(`【目标字数】约 ${programTargetWords} 字（中文汉字计）。`);
    userLines.push(
      mode === 'replace'
        ? '【任务】重写本章正文：在保留已有设定与前文脉络的前提下，输出全新的完整章节正文。'
        : '【任务】承接已有正文继续往下写，不要重复已有的句子，直接从新的内容写起。',
    );
    if (instruction !== '') {
      userLines.push(`【额外要求】${clip(instruction, 800)}`);
    }
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
            temperature: 0.9,
            maxTokens: estimateMaxTokens(programTargetWords),
          })) {
            if (delta === '') continue;
            accumulated += delta;
            controller.enqueue(encoder.encode(delta));
          }

          // 落库 + 记日志：任何失败都吞掉，不影响已经发出的流。
          try {
            if (accumulated.trim() !== '') {
              const content =
                mode === 'replace'
                  ? accumulated
                  : existingContent.trim() === ''
                    ? accumulated
                    : `${existingContent}\n\n${accumulated}`;
              updateChapter(chapterId, {
                content,
                wordCount: countWords(content),
                status: 'drafted',
              });
              logLlm({
                bookId,
                kind: 'generate',
                prompt: userPrompt,
                response: accumulated,
                elapsedMs: Date.now() - startedAt,
              });
              // 自动快照：落库成功后把生成结果存为 generate 版本，并裁剪历史。
              createChapterRevision({ chapterId, content, source: 'generate' });
              pruneChapterRevisions(chapterId, KEEP_REVISIONS);
            }
          } catch {
            // 保存 / 日志 / 快照失败一律忽略（例如磁盘只读），流仍按正常结束。
          }
        } catch (err) {
          const message =
            err instanceof LlmError
              ? err.message
              : err instanceof Error
                ? err.message
                : String(err);
          controller.enqueue(encoder.encode(`\n[生成中断] ${message}`));
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
