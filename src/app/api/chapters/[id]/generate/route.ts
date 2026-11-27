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
import { normalizeExcludeKeys, selectChapterContext } from '@/lib/chapter-context.js';

/** 默认目标字数。 */
const DEFAULT_TARGET_WORDS = 1200;
/** 目标字数下限 / 上限。 */
const MIN_TARGET_WORDS = 300;
const MAX_TARGET_WORDS = 4000;
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

/**
 * POST /api/chapters/[id]/generate —— 流式续写 / 重写章节正文。
 *
 * body: { instruction?: string, targetWords?: number, mode?: 'append' | 'replace' }
 * 响应：text/plain 流式正文；流结束后落库（content / wordCount / status）并写 llm_logs。
 *
 * 上下文（前情 / 设定 / 大纲 / 衔接正文 / 任务）全部由 selectChapterContext 组装，
 * 与只读预览接口 GET /api/chapters/[id]/context 共用同一份逻辑，保证「预览 = 实际注入」。
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
    const chapters: Array<Record<string, unknown>> = bookId === null ? [] : listChapters(bookId);
    const outlines: Array<Record<string, unknown>> = bookId === null ? [] : listOutlines(bookId);

    const existingContent = toText(chapter.content);

    // ---- 组装 prompt ----
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

    const context = selectChapterContext({
      book,
      bible,
      outlines,
      chapters,
      currentChapter: chapter,
      existingContent,
      targetWords: programTargetWords,
      mode,
      instruction,
      // exclude：数组或逗号分隔字符串（兼容 query 风格写法），非法值静默忽略。
      excludeKeys: normalizeExcludeKeys(body.exclude),
    });
    const userPrompt = context.promptText;

    const encoder = new TextEncoder();
    const startedAt = Date.now();
    let accumulated = '';

    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        // 客户端断开（req.signal abort）或流已关闭：此后不再写任何一段，直接结束。
        let clientGone = req.signal.aborted;

        /** 写一段正文：断开 / 流已关闭时静默返回 false，绝不抛出。 */
        const write = (text: string): boolean => {
          if (clientGone || req.signal.aborted) {
            clientGone = true;
            return false;
          }
          try {
            controller.enqueue(encoder.encode(text));
            return true;
          } catch {
            // Controller is already closed / ERR_INVALID_STATE / ERR_STREAM_WRITE_AFTER_END。
            clientGone = true;
            return false;
          }
        };

        try {
          for await (const delta of chatStream({
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: userPrompt },
            ],
            temperature: 0.9,
            maxTokens: estimateMaxTokens(programTargetWords),
            // 客户端断开时尽快中止上游 LLM 请求。
            signal: req.signal,
          })) {
            if (delta === '') continue;
            accumulated += delta;
            if (!write(delta)) break;
            if (req.signal.aborted) {
              clientGone = true;
              break;
            }
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
          // 客户端断开 / 流已关闭类异常：静默吞掉，不算生成失败、也不再往流里写。
          const aborted =
            req.signal.aborted ||
            (typeof err === 'object' &&
              err !== null &&
              (err as { name?: unknown }).name === 'AbortError') ||
            /ERR_INVALID_STATE|ERR_STREAM_WRITE_AFTER_END|Controller is already closed|already closed/i.test(
              message,
            );
          if (aborted) {
            clientGone = true;
          } else {
            write(`\n[生成中断] ${message}`);
          }
        } finally {
          try {
            controller.close();
          } catch {
            // 客户端已断开（Controller is already closed / ERR_INVALID_STATE）：忽略。
          }
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
