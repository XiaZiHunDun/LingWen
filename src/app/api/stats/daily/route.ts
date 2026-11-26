import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { dailyWordCounts, getDailyGoal } from '@/lib/repo.js';

/** 允许查询的最大天数。 */
const MAX_DAYS = 90;
/** 缺省天数。 */
const DEFAULT_DAYS = 14;

/**
 * GET /api/stats/daily?days=14
 * 返回 { days: [{date, words}], goal, todayWords }。
 */
export async function GET(req: Request) {
  try {
    initDb();

    const url = new URL(req.url);
    const raw = url.searchParams.get('days');
    const parsed = raw === null || raw.trim() === '' ? Number.NaN : Number(raw);
    const days =
      Number.isInteger(parsed) && parsed >= 1 && parsed <= MAX_DAYS ? parsed : DEFAULT_DAYS;

    const list = dailyWordCounts(days);
    const goal = getDailyGoal();
    // 双保险：即便上游聚合出现负值，对外也只暴露 0 以上的今日字数。
    const todayWords = list.length > 0 ? Math.max(0, list[list.length - 1].words) : 0;

    return NextResponse.json({ days: list, goal, todayWords });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
