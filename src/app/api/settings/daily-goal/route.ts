import { NextResponse } from 'next/server';
import { initDb } from '@/lib/db.js';
import { DAILY_GOAL_MAX, DAILY_GOAL_MIN, setDailyGoal } from '@/lib/repo.js';

/**
 * PUT /api/settings/daily-goal
 * body { goal: number }，校验 1..20000 后返回 { goal }；非法值 400。
 */
export async function PUT(req: Request) {
  try {
    initDb();

    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
    const rawGoal = body.goal;
    const goal =
      typeof rawGoal === 'number'
        ? rawGoal
        : typeof rawGoal === 'string' && rawGoal.trim() !== ''
          ? Number(rawGoal)
          : Number.NaN;

    if (!Number.isInteger(goal) || goal < DAILY_GOAL_MIN || goal > DAILY_GOAL_MAX) {
      return NextResponse.json(
        { error: `目标必须是 ${DAILY_GOAL_MIN}..${DAILY_GOAL_MAX} 之间的整数` },
        { status: 400 },
      );
    }

    const saved = setDailyGoal(goal);
    return NextResponse.json({ goal: saved });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
