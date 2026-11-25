import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { getBook, listBible, listOutlines, replaceOutlines, logLlm } from '@/lib/repo.js';
import { chat, isLlmConfigured, LlmError } from '@/lib/llm.js';

/** 大纲条目（写入 outlines 表时只用到 seq / title / summary）。 */
interface OutlineItem {
  seq: number;
  title: string;
  summary: string;
}

/** replaceOutlines 接受的入参形状（与 repo.js 的 JSDoc 保持一致）。 */
type OutlineInput = Array<{
  seq?: number | null;
  title?: string | null;
  summary?: string | null;
  status?: string | null;
}>;

const DEFAULT_CHAPTERS = 8;
const MIN_CHAPTERS = 3;
const MAX_CHAPTERS = 30;
const MAX_TOKENS = 2500;
const DETAIL_LIMIT = 300;

/** 解析章节数：缺省 8，非法值回退默认，合法值 clamp 到 3..30。 */
function resolveChapterCount(value: unknown): number {
  if (value === undefined || value === null) return DEFAULT_CHAPTERS;
  const raw = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(raw)) return DEFAULT_CHAPTERS;
  return Math.min(MAX_CHAPTERS, Math.max(MIN_CHAPTERS, Math.trunc(raw)));
}

/** 去掉 ```json / ``` 代码块包裹。 */
function stripCodeFence(text: string): string {
  let out = text.trim();
  if (out.startsWith('```')) {
    out = out.replace(/^```[A-Za-z0-9_-]*[ \t]*\r?\n?/, '');
    out = out.replace(/\r?\n?```$/, '');
  }
  return out.trim();
}

/** 过滤非法项，并按顺序补齐 seq = index + 1。 */
function normalizeItems(list: unknown[]): OutlineItem[] {
  const out: OutlineItem[] = [];
  for (const entry of list) {
    if (entry === null || typeof entry !== 'object' || Array.isArray(entry)) continue;
    const record = entry as Record<string, unknown>;
    const title = typeof record.title === 'string' ? record.title.trim() : '';
    const summary = typeof record.summary === 'string' ? record.summary.trim() : '';
    if (title === '' && summary === '') continue;
    out.push({ seq: out.length + 1, title, summary });
  }
  return out;
}

/**
 * 从模型原始文本中解析大纲数组：
 * 先 trim → 去代码块 → 截取第一个 '[' 到最后一个 ']' → JSON.parse。
 * 失败或结果为空数组时返回 undefined。
 */
function parseOutlineText(text: string): OutlineItem[] | undefined {
  const cleaned = stripCodeFence(text);
  const start = cleaned.indexOf('[');
  const end = cleaned.lastIndexOf(']');
  if (start === -1 || end === -1 || end <= start) return undefined;
  const slice = cleaned.slice(start, end + 1);
  let parsed: unknown;
  try {
    parsed = JSON.parse(slice) as unknown;
  } catch {
    return undefined;
  }
  if (!Array.isArray(parsed)) return undefined;
  const items = normalizeItems(parsed as unknown[]);
  return items.length > 0 ? items : undefined;
}

/** 把设定集条目格式化为提示词里的纯文本列表。 */
function formatBible(entries: Array<Record<string, unknown>>): string {
  if (entries.length === 0) return '（暂无设定）';
  return entries
    .map((entry) => {
      const category = typeof entry.category === 'string' ? entry.category : '未分类';
      const title = typeof entry.title === 'string' ? entry.title : '';
      const content = typeof entry.content === 'string' ? entry.content : '';
      return `- [${category}] ${title}：${content}`;
    })
    .join('\n');
}

/** GET /api/books/[id]/outline —— 列出某本书的大纲。 */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = Number(id);
    if (Number.isNaN(bookId)) {
      return NextResponse.json({ error: 'id 非法' }, { status: 400 });
    }
    const book = getBook(bookId);
    if (book === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }
    return NextResponse.json({ outlines: listOutlines(bookId) });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}

/** POST /api/books/[id]/outline —— 手工覆盖大纲，或调用 LLM 生成大纲。 */
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    initDb();
    const { id } = await params;
    const bookId = Number(id);
    if (Number.isNaN(bookId)) {
      return NextResponse.json({ error: 'id 非法' }, { status: 400 });
    }

    const book = getBook(bookId);
    if (book === undefined) {
      return NextResponse.json({ error: '书籍不存在' }, { status: 404 });
    }

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;

    // 模式 a：手工提交大纲，直接整体覆盖。
    if (Array.isArray(body.outlines)) {
      const outlines = replaceOutlines(bookId, body.outlines as OutlineInput);
      return NextResponse.json({ outlines, mode: 'manual' });
    }

    // 模式 b：由 LLM 生成大纲。
    if (body.generate === true) {
      if (!isLlmConfigured()) {
        return NextResponse.json({ error: 'LLM 未配置：请设置 OPENAI_API_KEY' }, { status: 400 });
      }

      const chapterCount = resolveChapterCount(body.chapters);
      const bible = listBible(bookId);
      const title = typeof book.title === 'string' ? book.title : '';
      const genre = typeof book.genre === 'string' ? book.genre : '';
      const summary = typeof book.summary === 'string' ? book.summary : '';
      const style = typeof book.style === 'string' ? book.style : '';

      const system =
        '你是资深中文小说策划编辑。你只输出 JSON，不输出任何解释文字、Markdown 标题或注释。';
      const user = [
        `请为下面这本书生成分章大纲，共 ${chapterCount} 章。`,
        `书名：${title || '（未命名）'}`,
        genre ? `类型：${genre}` : '',
        style ? `文风：${style}` : '',
        summary ? `简介：${summary}` : '',
        '设定集：',
        formatBible(bible),
        '要求：只输出 JSON 数组，元素形如 {"seq":1,"title":"...","summary":"..."}，',
        `共 ${chapterCount} 章（默认 8 章，clamp 到 3..30），不要任何解释文字。`,
      ]
        .filter((line) => line !== '')
        .join('\n');

      const startedAt = Date.now();
      try {
        const raw = await chat({
          messages: [
            { role: 'system', content: system },
            { role: 'user', content: user },
          ],
          temperature: 0.7,
          maxTokens: MAX_TOKENS,
        });
        const elapsedMs = Date.now() - startedAt;

        const normalized = parseOutlineText(raw);
        if (normalized === undefined) {
          return NextResponse.json(
            { error: '大纲解析失败', detail: raw.slice(0, DETAIL_LIMIT) },
            { status: 502 },
          );
        }

        const outlines = replaceOutlines(bookId, normalized);
        logLlm({
          bookId,
          kind: 'outline',
          prompt: user,
          response: raw,
          elapsedMs,
        });
        return NextResponse.json({ outlines, mode: 'llm' });
      } catch (err) {
        if (err instanceof LlmError) {
          return NextResponse.json({ error: err.message }, { status: 502 });
        }
        throw err;
      }
    }

    return NextResponse.json(
      { error: '请求体需包含 outlines 数组或 generate: true' },
      { status: 400 },
    );
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
