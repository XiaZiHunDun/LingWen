import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { dailyWordCounts } from '@/lib/repo.js';
import {
  DEFAULT_DAYS,
  MAX_DAYS,
  MIN_DAYS,
  buildDailyStatsCsv,
  parseDaysParam,
} from '@/lib/stats-csv.js';

/**
 * GET /api/stats/export?days=30
 * 导出最近 N 天每日净字数为 CSV（UTF-8 BOM，表头「日期,字数」）。
 *
 * 字数口径复用 repo.dailyWordCounts()，与 /stats 页面完全一致。
 * days 校验失败 → 400；其余异常 → 500。
 */
export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const days = parseDaysParam(url.searchParams.get('days'));
    if (days === null) {
      return NextResponse.json(
        { error: `days 必须是 ${MIN_DAYS}-${MAX_DAYS} 的整数（默认 ${DEFAULT_DAYS}）` },
        { status: 400 },
      );
    }

    initDb();
    const rows = dailyWordCounts(days);
    const csv = buildDailyStatsCsv(rows, days);

    return new Response(csv, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="lingwen-stats-${days}days.csv"`,
        'Cache-Control': 'no-store',
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
