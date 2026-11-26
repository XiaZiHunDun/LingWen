import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, getChapter, listBible, logLlm } from '@/lib/repo.js';
import { chat, isLlmConfigured, LlmError } from '@/lib/llm.js';

/** 问题级别：error = 严重问题，warn = 建议优化。 */
type IssueLevel = 'error' | 'warn';

/** 单个检查问题。 */
interface Issue {
  level: IssueLevel;
  quote: string;
  suggestion: string;
}

/** 正文注入 prompt 时最多多少字符。 */
const MAX_PROMPT_CONTENT = 2000;
/** 单条设定 / 摘要注入 prompt 的最大长度（字符）。 */
const MAX_SNIPPET = 300;
/** 解析失败时回显模型原文的最大长度。 */
const MAX_DETAIL = 300;
/** 最多返回多少条问题（prompt 中已要求，这里只做说明用）。 */
const MAX_ISSUES = 6;
/** 首次调用的 token 预算：需容纳推理过程 + JSON 结果。 */
const FIRST_MAX_TOKENS = 3000;
/** 首次返回内容为空时的重试预算（推理可能吃掉全部预算）。 */
const RETRY_MAX_TOKENS = 4000;

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

/** 去掉 ```json / ``` 围栏，只保留中间文本。 */
function stripFence(text: string): string {
  const trimmed = text.trim();
  if (!trimmed.startsWith('```')) return trimmed;
  const withoutHead = trimmed.replace(/^```[A-Za-z]*\s*/, '');
  const endIndex = withoutHead.lastIndexOf('```');
  return (endIndex === -1 ? withoutHead : withoutHead.slice(0, endIndex)).trim();
}

/** 把单个未知元素归一成 Issue；不可用时返回 null。 */
function toIssue(value: unknown): Issue | null {
  if (typeof value !== 'object' || value === null) return null;
  const record = value as Record<string, unknown>;
  const quote = toText(record.quote).trim();
  const suggestion = toText(record.suggestion).trim();
  if (quote === '' && suggestion === '') return null;
  const level: IssueLevel = record.level === 'error' ? 'error' : 'warn';
  return { level, quote, suggestion };
}

/**
 * 解析模型返回的 JSON；失败返回 null（调用方回 502）。
 * 容错：去围栏 → 取第一个 { 到最后一个 } → JSON.parse；issues 非数组按空数组。
 */
function parseReview(raw: string): { issues: Issue[] } | null {
  const text = stripFence(raw);
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end === -1 || end < start) return null;

  let parsed: unknown;
  try {
    parsed = JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
  if (typeof parsed !== 'object' || parsed === null) return null;

  const list = (parsed as Record<string, unknown>).issues;
  if (!Array.isArray(list)) return { issues: [] };

  const issues: Issue[] = [];
  for (const item of list) {
    const issue = toIssue(item);
    if (issue !== null) issues.push(issue);
  }
  return { issues };
}

/**
 * POST /api/chapters/[id]/review —— 用大模型检查章节正文（非流式）。
 *
 * 响应：{ issues: Issue[], summary: string }；解析失败 502，其他异常 500。
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

    const content = toText(chapter.content).trim();
    if (content === '') {
      return NextResponse.json({ error: '章节还没有正文' }, { status: 400 });
    }

    if (!isLlmConfigured()) {
      return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
    }

    const bookId = toNumber(chapter.bookId);
    const book = bookId === null ? undefined : getBook(bookId);
    const bible = bookId === null ? [] : listBible(bookId);

    // ---- 组装 prompt ----
    const contextLines: string[] = [];
    if (book !== undefined) {
      const title = toText(book.title);
      const genre = toText(book.genre);
      const style = toText(book.style);
      const summary = toText(book.summary);
      if (title) contextLines.push(`书名：${title}`);
      if (genre) contextLines.push(`类型：${genre}`);
      if (style) contextLines.push(`风格：${style}`);
      if (summary) contextLines.push(`全书简介：${clip(summary)}`);
    }

    const bibleLines = bible
      .map((item) => {
        const category = toText(item.category);
        const title = toText(item.title);
        const itemContent = toText(item.content);
        const head = [category, title].filter((part) => part !== '').join('·');
        if (head === '' && itemContent === '') return '';
        return `- ${head === '' ? '设定' : head}：${clip(itemContent)}`;
      })
      .filter((line) => line !== '');

    const systemPrompt = [
      '你是一位中文小说编辑，负责审读章节正文并指出问题。',
      '硬性要求：',
      '1. 只输出 JSON，不输出任何解释、前言、结语或 Markdown 围栏。',
      `2. 最多找出 ${MAX_ISSUES} 个问题，按严重程度从高到低排序。`,
      '3. 输出格式：{"issues":[{"level":"error"|"warn","quote":"原文片段(<=30字)","suggestion":"具体修改建议"}]}',
      '4. level 只能是 "error"（严重问题，必须改）或 "warn"（建议优化）。',
      '5. quote 必须逐字摘自正文，长度不超过 30 字；suggestion 要具体、可直接照做。',
      '6. 没有问题时只输出 {"issues":[]}。',
    ].join('\n');

    const userLines: string[] = [];
    if (contextLines.length > 0) userLines.push(`【书籍信息】\n${contextLines.join('\n')}`);
    if (bibleLines.length > 0) {
      userLines.push(`【设定集】\n${bibleLines.slice(0, 20).join('\n')}`);
    }
    const chapterTitle = toText(chapter.title) || `第 ${chapterId} 章`;
    userLines.push(`【本章标题】${chapterTitle}`);
    userLines.push(`【正文】\n${content.slice(0, MAX_PROMPT_CONTENT)}`);
    if (content.length > MAX_PROMPT_CONTENT) {
      userLines.push(`（正文较长，以上仅前 ${MAX_PROMPT_CONTENT} 字。）`);
    }
    userLines.push(
      '【任务】检查上面正文的问题（人物 / 设定前后矛盾、逻辑漏洞、语句不通、节奏拖沓、表达重复等），' +
        '按 system 指定的 JSON 格式输出，不要输出任何解释文字。',
    );
    const userPrompt = userLines.join('\n\n');

    const messages = [
      { role: 'system' as const, content: systemPrompt },
      { role: 'user' as const, content: userPrompt },
    ];

    const startedAt = Date.now();
    let raw = await chat({
      messages,
      temperature: 0.3,
      maxTokens: FIRST_MAX_TOKENS,
    });
    // 模型可能先输出 reasoning 把预算耗尽，导致 content 为空：放大预算重试一次。
    if (raw.trim() === '') {
      raw = await chat({
        messages,
        temperature: 0.3,
        maxTokens: RETRY_MAX_TOKENS,
      });
    }
    // 重试后仍为空：走专用错误，不落到「检查结果解析失败」分支。
    if (raw.trim() === '') {
      return NextResponse.json({ error: '模型未返回内容，请重试' }, { status: 502 });
    }
    const elapsedMs = Date.now() - startedAt;

    const parsed = parseReview(raw);
    if (parsed === null) {
      return NextResponse.json(
        { error: '检查结果解析失败', detail: raw.slice(0, MAX_DETAIL) },
        { status: 502 },
      );
    }

    const issues = parsed.issues;
    logLlm({
      bookId,
      kind: 'review',
      prompt: content.slice(0, MAX_PROMPT_CONTENT),
      response: raw,
      elapsedMs,
    });

    return NextResponse.json({ issues, summary: `共 ${issues.length} 条` });
  } catch (err) {
    const message = err instanceof LlmError ? err.message : err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
