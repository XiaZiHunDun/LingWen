import { initDb } from '@/lib/db.js';
import { getBook, listChapters } from '@/lib/repo.js';

/** 支持的导出格式。 */
type ExportFormat = 'md' | 'txt';

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** 文本字段：非字符串按空串处理。 */
function text(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

/** 标题字段：空串时给出兜底文案。 */
function titleOr(value: unknown, fallback: string): string {
  const raw = text(value).trim();
  return raw === '' ? fallback : raw;
}

/** 章节序号：优先用 seq，非法时退回顺序号。 */
function chapterSeq(value: unknown, index: number): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  return index + 1;
}

/** 生成 Markdown 正文。 */
function buildMarkdown(book: Record<string, unknown>, chapters: Array<Record<string, unknown>>): string {
  const title = titleOr(book.title, '未命名');
  const genre = text(book.genre).trim();
  const summary = text(book.summary).trim();

  const lines: string[] = [`# ${title}`];
  if (genre !== '') lines.push(`> 类型：${genre}`);
  if (summary !== '') lines.push(`> 简介：${summary}`);
  lines.push('');

  chapters.forEach((chapter, index) => {
    const seq = chapterSeq(chapter.seq, index);
    const chapterTitle = titleOr(chapter.title, '未命名');
    lines.push(`## 第 ${seq} 章 ${chapterTitle}`);
    lines.push('');
    const content = text(chapter.content);
    if (content !== '') lines.push(content);
    lines.push('');
  });

  return lines.join('\n').trimEnd() + '\n';
}

/** 生成纯文本正文。 */
function buildText(book: Record<string, unknown>, chapters: Array<Record<string, unknown>>): string {
  const title = titleOr(book.title, '未命名');
  const sections: string[] = [];

  chapters.forEach((chapter, index) => {
    const seq = chapterSeq(chapter.seq, index);
    const chapterTitle = titleOr(chapter.title, '未命名');
    const content = text(chapter.content);
    const section = content === ''
      ? `第 ${seq} 章 ${chapterTitle}`
      : `第 ${seq} 章 ${chapterTitle}\n${content}`;
    sections.push(section);
  });

  // 首行书名，之后每章之间空两行。
  return [`${title}`, ...sections].join('\n\n\n') + '\n';
}

/** GET /api/books/[id]/export?format=md|txt —— 导出整本书。 */
export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  initDb();
  try {
    const { id } = await params;
    const bookId = parseId(id);
    if (bookId === null) {
      return new Response(JSON.stringify({ error: 'id 非法：必须是数字' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      });
    }

    const book = getBook(bookId);
    if (book === undefined) {
      return new Response(JSON.stringify({ error: '书籍不存在' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      });
    }

    const rawFormat = new URL(req.url).searchParams.get('format');
    const format: ExportFormat = rawFormat === 'txt' ? 'txt' : 'md';

    const chapters = listChapters(bookId);
    const title = titleOr(book.title, '未命名');
    const body = format === 'md' ? buildMarkdown(book, chapters) : buildText(book, chapters);

    return new Response(body, {
      headers: {
        'Content-Type':
          format === 'md' ? 'text/markdown; charset=utf-8' : 'text/plain; charset=utf-8',
        'Content-Disposition': `attachment; filename*=UTF-8''${encodeURIComponent(title)}.${format}`,
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : String(err) }),
      { status: 500, headers: { 'Content-Type': 'application/json; charset=utf-8' } },
    );
  }
}
