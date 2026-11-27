import { buildChapterExport } from '@/lib/chapter-export.js';
import { initDb } from '@/lib/db.js';
import { getChapter } from '@/lib/repo.js';

/** 解析路由段的 id：必须是有限整数，否则返回 null（调用方回 400）。 */
function parseId(raw: string): number | null {
  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) return null;
  return value;
}

/** GET /api/chapters/[id]/export?format=md|txt —— 导出单章。 */
export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  initDb();
  try {
    const { id } = await params;
    const chapterId = parseId(id);
    if (chapterId === null) {
      return new Response(JSON.stringify({ error: 'id 非法：必须是数字' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      });
    }

    const chapter = getChapter(chapterId);
    if (!chapter) {
      return new Response(JSON.stringify({ error: '章节不存在' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      });
    }

    // 与整书导出同口径：只有 'txt' 才按 txt，其余（含缺省、非法值）都是 md。
    const rawFormat = new URL(req.url).searchParams.get('format');
    const { body, contentType, filename } = buildChapterExport(chapter, rawFormat);

    return new Response(body, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `attachment; filename*=UTF-8''${filename}`,
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : String(err) }),
      { status: 500, headers: { 'Content-Type': 'application/json; charset=utf-8' } },
    );
  }
}
