import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import {
  createChapter,
  createChapterRevision,
  getBook,
  listBible,
  listChapters,
  listOutlines,
  logLlm,
  pruneChapterRevisions,
  updateChapter,
} from '@/lib/repo.js';
import { countWords } from '@/lib/wordcount.js';
import { chatStream, isLlmConfigured, LlmError } from '@/lib/llm.js';

/** 默认目标字数（与单章 generate 路由保持一致）。 */
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
/** 每个章节保留的历史版本条数。 */
const KEEP_REVISIONS = 20;
/** 单次一键续写的章节数下限 / 上限。 */
const MIN_BATCH_COUNT = 1;
const MAX_BATCH_COUNT = 5;

/** 一条待续写的大纲。 */
type PendingOutline = { id: number; title: string; summary: string };

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

/** 续写章节数：缺省 / 非法值按 1 处理，其余 clamp 到 [1, 5]。 */
function clampCount(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return MIN_BATCH_COUNT;
  const rounded = Math.round(value);
  return Math.min(MAX_BATCH_COUNT, Math.max(MIN_BATCH_COUNT, rounded));
}

/**
 * 判断是否为「响应流已关闭 / 已中止」类异常。
 * 客户端断开后往流里写会抛这些（Next/Node 侧文案不统一），一律视为正常断开、静默吞掉。
 */
function isStreamClosedError(err: unknown): boolean {
  if (err === null || err === undefined) return false;
  if (typeof err === 'object' && (err as { name?: unknown }).name === 'AbortError') return true;
  const message = err instanceof Error ? err.message : String(err);
  return /ERR_INVALID_STATE|ERR_STREAM_WRITE_AFTER_END|Controller is already closed|already closed/i.test(
    message,
  );
}

/** 取已有章节里最大的 seq（没有则 0），用于自动生成新 seq。 */
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

/** 选出本书尚未建章的大纲：outlines 里 id 未出现在 chapters.outline_id 的记录，按 seq 取前 count 条。 */
function pickPendingOutlines(
  allOutlines: Array<Record<string, unknown>>,
  chapters: Array<Record<string, unknown>>,
  count: number,
): PendingOutline[] {
  const built = new Set<number>();
  for (const row of chapters) {
    const outlineId = toNumber(row.outlineId);
    if (outlineId !== null) built.add(outlineId);
  }
  const pending: PendingOutline[] = [];
  for (const row of allOutlines) {
    const outlineId = toNumber(row.id);
    if (outlineId === null || built.has(outlineId)) continue;
    pending.push({
      id: outlineId,
      title: toText(row.title),
      summary: toText(row.summary),
    });
    if (pending.length >= count) break;
  }
  return pending;
}

/**
 * 组装单章正文的 system / user prompt。
 * 提示词与 /api/chapters/[id]/generate 完全一致（新章正文为空，故不带「衔接上文」段）。
 */
function buildChapterPrompts(params: {
  book: Record<string, unknown> | undefined;
  bible: Array<Record<string, unknown>>;
  previous: Array<{ title: string; summary: string }>;
  outline: PendingOutline;
  chapterTitle: string;
  targetWords: number;
}): { systemPrompt: string; userPrompt: string } {
  const { book, bible, previous, outline, chapterTitle, targetWords } = params;

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

  const outlineLines: string[] = [];
  if (outline.title !== '') outlineLines.push(`标题：${outline.title}`);
  const outlineSummary = clip(outline.summary, MAX_OUTLINE_SUMMARY);
  if (outlineSummary !== '') outlineLines.push(`摘要：${outlineSummary}`);

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
  userLines.push(`【目标字数】约 ${targetWords} 字（中文汉字计）。`);
  userLines.push('【任务】承接已有正文继续往下写，不要重复已有的句子，直接从新的内容写起。');
  const userPrompt = userLines.join('\n\n');

  return { systemPrompt, userPrompt };
}

/**
 * POST /api/books/[id]/chapters/generate-batch —— 一键续写接下来 N 章。
 *
 * body: { count?: number }（默认 1，clamp 到 1-5，非法值按默认处理）
 * 响应：application/x-ndjson 流，每行一个 JSON 事件：
 *   {"type":"start","chapterId","title"}
 *   {"type":"delta","chapterId","text"}
 *   {"type":"chapter-done","chapterId","wordCount"}
 *   {"type":"done","created":n}
 *   {"type":"error","message"}
 * 每章：先建空章（语义同 POST /api/books/[id]/chapters），再流式生成正文并落库（content / wordCount）。
 * 客户端断开（request.signal abort）时停止后续章节，已生成内容保留。
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

    if (!isLlmConfigured()) {
      return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
    const count = clampCount(body.count);
    const targetWords = clampTargetWords(body.targetWords);

    const encoder = new TextEncoder();
    const encodeLine = (event: Record<string, unknown>): Uint8Array =>
      encoder.encode(`${JSON.stringify(event)}\n`);

    // 断开信号汇聚：req.signal abort 或响应流被 cancel，任一发生即视为客户端已走。
    // 用内部 AbortController，既能同步给上游 LLM 流式请求，也能被 cancel() 触发。
    const goneController = new AbortController();
    const goneSignal = goneController.signal;
    const markGone = (): void => {
      if (!goneSignal.aborted) goneController.abort();
    };
    if (req.signal.aborted) {
      markGone();
    } else {
      req.signal.addEventListener('abort', markGone, { once: true });
    }

    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        let created = 0;
        // 客户端已断开（signal abort 或写流失败）：此后不写任何事件、不再开新章。
        let clientGone = false;

        /** 写一条事件：断开 / 流已关闭时静默返回 false，绝不抛出。 */
        const send = (event: Record<string, unknown>): boolean => {
          // 每次写事件前先查断开信号（req.signal 或响应流被 cancel），断开后不再写任何事件。
          if (clientGone || req.signal.aborted || goneSignal.aborted) {
            clientGone = true;
            return false;
          }
          try {
            controller.enqueue(encodeLine(event));
            return true;
          } catch {
            // 例如 Controller is already closed / ERR_INVALID_STATE / ERR_STREAM_WRITE_AFTER_END。
            clientGone = true;
            return false;
          }
        };

        try {
          const pending = pickPendingOutlines(
            listOutlines(bookId) as Array<Record<string, unknown>>,
            listChapters(bookId) as Array<Record<string, unknown>>,
            count,
          );

          if (pending.length === 0) {
            send({ type: 'done', created: 0, reason: '没有待续写的大纲' });
            return;
          }

          const bible = listBible(bookId) as Array<Record<string, unknown>>;

          for (const outline of pending) {
            // 客户端已断开：不再开新章，直接结束整批。
            if (clientGone || goneSignal.aborted) {
              clientGone = true;
              break;
            }

            // 1) 按 createChapter 语义建空章（seq 递增，正文空串，wordCount 由表默认 0 兜底）。
            const chaptersNow = listChapters(bookId) as Array<Record<string, unknown>>;
            let chapterId: number | null = null;
            try {
              const createdRow = createChapter({
                bookId,
                outlineId: outline.id,
                seq: maxSeq(chaptersNow) + 1,
                title: outline.title,
                summary: outline.summary,
                content: '',
              }) as Record<string, unknown> | undefined;
              chapterId = createdRow === undefined ? null : toNumber(createdRow.id);
            } catch {
              chapterId = null;
            }
            if (chapterId === null) {
              if (!send({ type: 'error', message: '创建章节失败' })) break;
              continue;
            }

            const chapterTitle = outline.title !== '' ? outline.title : `第 ${chapterId} 章`;
            if (!send({ type: 'start', chapterId, title: chapterTitle })) break;

            // 2) 组装 prompt（提示词口径与单章 generate 路由一致）。
            const afterCreate = listChapters(bookId) as Array<Record<string, unknown>>;
            const { systemPrompt, userPrompt } = buildChapterPrompts({
              book,
              bible,
              previous: pickPreviousChapters(afterCreate, chapterId),
              outline,
              chapterTitle,
              targetWords,
            });

            // 3) 流式生成：边生成边推 delta 事件。
            const startedAt = Date.now();
            let accumulated = '';
            let llmError: string | null = null;
            try {
              for await (const delta of chatStream({
                messages: [
                  { role: 'system', content: systemPrompt },
                  { role: 'user', content: userPrompt },
                ],
                temperature: 0.9,
                maxTokens: estimateMaxTokens(targetWords),
                // 客户端断开（goneSignal abort）时尽快中止上游 LLM 请求。
                signal: goneSignal,
              })) {
                if (delta === '') continue;
                accumulated += delta;
                // 用户取消 / 写流失败：立刻停止本章剩余生成（已生成部分照常落库）。
                if (!send({ type: 'delta', chapterId, text: delta })) break;
                if (goneSignal.aborted) break;
              }
            } catch (err) {
              if (goneSignal.aborted || isStreamClosedError(err)) {
                // 客户端断开导致的中止 / 流已关闭：静默处理，不算 LLM 失败、不写事件。
                clientGone = true;
              } else {
                llmError =
                  err instanceof LlmError
                    ? err.message
                    : err instanceof Error
                      ? err.message
                      : String(err);
              }
            }

            // 4) 落库：content + wordCount（失败也不影响已发出的流）。
            let wordCount = 0;
            if (accumulated.trim() !== '') {
              wordCount = countWords(accumulated);
              try {
                updateChapter(chapterId, {
                  content: accumulated,
                  wordCount,
                  status: 'drafted',
                });
                logLlm({
                  bookId,
                  kind: 'generate',
                  prompt: userPrompt,
                  response: accumulated,
                  elapsedMs: Date.now() - startedAt,
                });
                createChapterRevision({ chapterId, content: accumulated, source: 'generate' });
                pruneChapterRevisions(chapterId, KEEP_REVISIONS);
              } catch {
                // 保存 / 日志 / 快照失败一律忽略（例如磁盘只读）。
              }
            }

            // 本章已落库：即使随后发现客户端已断开，也保留已写入内容（不删章）。
            created += 1;
            if (!send({ type: 'chapter-done', chapterId, wordCount })) break;

            if (llmError !== null) {
              send({ type: 'error', message: llmError });
              break;
            }
            if (clientGone || goneSignal.aborted) {
              clientGone = true;
              break;
            }
          }

          send({ type: 'done', created });
        } catch (err) {
          // 兜底：流已关闭类异常静默吞掉；其它异常仍尽量上报一条 error + done。
          if (!isStreamClosedError(err)) {
            send({ type: 'error', message: err instanceof Error ? err.message : String(err) });
            send({ type: 'done', created });
          }
        } finally {
          try {
            controller.close();
          } catch {
            // 客户端已断开（Controller is already closed / ERR_INVALID_STATE）：忽略。
          }
        }
      },
      cancel() {
        // 消费端（客户端）断开：立刻中止当前章生成，不再创建后续章节。
        markGone();
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'application/x-ndjson; charset=utf-8',
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
