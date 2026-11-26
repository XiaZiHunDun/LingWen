import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { monthlyWordCounts } from '@/lib/repo.js';

/** 月份格式：YYYY-MM，月份限定 01..12。 */
const MONTH_PATTERN = /^(\d{4})-(0[1-9]|1[0-2])$/;

/** 取本地当月的 YYYY-MM 字符串。 */
function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * GET /api/stats/month?month=YYYY-MM
 * 返回 { month, days: [{date, words}], total, activeDays, bestDay }。
 * month 缺省为当月；格式非法返回 400。
 */
export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const raw = url.searchParams.get('month');
    const month = raw === null || raw.trim() === '' ? currentMonth() : raw.trim();
    if (!MONTH_PATTERN.test(month)) {
      return NextResponse.json(
        { error: 'month 参数格式应为 YYYY-MM（例如 2024-05）' },
        { status: 400 },
      );
    }

    initDb();
    const summary = monthlyWordCounts(month);
    return NextResponse.json(summary);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
