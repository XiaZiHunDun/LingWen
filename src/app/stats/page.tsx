'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';

/** 每日字数点（/api/stats/daily、/api/stats/month 的 days 元素）。 */
interface DailyPoint {
  date: string;
  words: number;
}

/** /api/books 返回的书籍条目（只用到 id 与 title）。 */
interface BookBrief {
  id: number;
  title: string;
}

/** /api/books/[id]/stats 返回的单书统计，外加 id / title 组成对比行。 */
interface BookRow {
  id: number;
  title: string;
  chapterCount: number;
  doneChapterCount: number;
  totalWords: number;
  outlineCount: number;
  bibleCount: number;
}

/** /api/stats 返回的全局统计。 */
interface Overview {
  bookCount: number;
  chapterCount: number;
  totalWords: number;
  outlineCount: number;
  bibleCount: number;
}

/** /api/stats/month 返回的月度汇总。 */
interface MonthSummary {
  month: string;
  total: number;
  activeDays: number;
  bestDay: DailyPoint | null;
}

/** 安全取数字：非 number / 非有限数一律回退。 */
function num(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

/** 千分位格式化，避免每处重复写字面量。 */
function fmt(value: number): string {
  return value.toLocaleString('zh-CN');
}

/** 从任意 JSON 值里解析 [{date, words}]，非法项直接丢弃。 */
function readDays(value: unknown): DailyPoint[] {
  if (!Array.isArray(value)) return [];
  const out: DailyPoint[] = [];
  for (const item of value) {
    if (item === null || typeof item !== 'object') continue;
    const row = item as Record<string, unknown>;
    const date = typeof row.date === 'string' ? row.date : '';
    if (date === '') continue;
    out.push({ date, words: num(row.words) });
  }
  return out;
}

/** 从对象里取嵌套的 stats 字段（非法时返回 null）。 */
function readStatsObject(payload: unknown): Record<string, unknown> | null {
  if (payload === null || typeof payload !== 'object') return null;
  const raw = (payload as { stats?: unknown }).stats;
  if (raw === null || typeof raw !== 'object') return null;
  return raw as Record<string, unknown>;
}

/**
 * 连续写作天数：与书架页口径一致——今天为 0 则从昨天往前数，遇到 0 字那天即停止。
 */
function computeStreak(days: ReadonlyArray<DailyPoint>): number {
  let index = days.length - 1;
  if (index < 0) return 0;
  if (days[index].words <= 0) index -= 1;
  let count = 0;
  while (index >= 0 && days[index].words > 0) {
    count += 1;
    index -= 1;
  }
  return count;
}

export default function StatsPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  // 近 14 天柱状图数据（取自 days=90 响应的末 14 项）。
  const [days, setDays] = useState<DailyPoint[]>([]);
  const [todayWords, setTodayWords] = useState(0);
  const [goal, setGoal] = useState(1000);
  const [streak, setStreak] = useState(0);
  const [bookRows, setBookRows] = useState<BookRow[]>([]);
  const [bookCount, setBookCount] = useState(0);
  const [month, setMonth] = useState<MonthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const [statsRes, dailyRes, monthRes, booksRes] = await Promise.all([
        fetch('/api/stats'),
        fetch('/api/stats/daily?days=90'),
        fetch('/api/stats/month'),
        fetch('/api/books'),
      ]);

      // 全局概览：作品数 / 章节总数 / 总字数。
      if (statsRes.ok) {
        const stats = readStatsObject(await statsRes.json());
        if (stats !== null) {
          setOverview({
            bookCount: num(stats.bookCount),
            chapterCount: num(stats.chapterCount),
            totalWords: num(stats.totalWords),
            outlineCount: num(stats.outlineCount),
            bibleCount: num(stats.bibleCount),
          });
        }
      }

      // 每日字数：90 天窗口用于连续天数，末 14 天用于柱状图。
      if (dailyRes.ok) {
        const data: unknown = await dailyRes.json();
        const source =
          data !== null && typeof data === 'object' ? (data as Record<string, unknown>) : {};
        const allDays = readDays(source.days);
        setDays(allDays.slice(-14));
        setStreak(computeStreak(allDays));
        setTodayWords(num(source.todayWords));
        setGoal(num(source.goal, 1000));
      }

      // 本月小结。
      if (monthRes.ok) {
        const data: unknown = await monthRes.json();
        const source =
          data !== null && typeof data === 'object' ? (data as Record<string, unknown>) : {};
        const bestRaw = source.bestDay;
        let bestDay: DailyPoint | null = null;
        if (bestRaw !== null && typeof bestRaw === 'object') {
          const row = bestRaw as Record<string, unknown>;
          const date = typeof row.date === 'string' ? row.date : '';
          if (date !== '') bestDay = { date, words: num(row.words) };
        }
        setMonth({
          month: typeof source.month === 'string' ? source.month : '',
          total: num(source.total),
          activeDays: num(source.activeDays),
          bestDay,
        });
      }

      // 作品对比：先拿列表，再并发请求每本书的 stats。
      if (booksRes.ok) {
        const data: unknown = await booksRes.json();
        const rawList =
          data !== null && typeof data === 'object' && 'books' in data
            ? (data as { books?: unknown }).books
            : undefined;
        const briefs: BookBrief[] = [];
        if (Array.isArray(rawList)) {
          for (const item of rawList) {
            if (item === null || typeof item !== 'object') continue;
            const row = item as Record<string, unknown>;
            const id = num(row.id, Number.NaN);
            const title = typeof row.title === 'string' ? row.title : '';
            if (!Number.isFinite(id)) continue;
            briefs.push({ id, title });
          }
        }
        setBookCount(briefs.length);

        const results = await Promise.all(
          briefs.map(async (brief): Promise<BookRow | null> => {
            try {
              const res = await fetch(`/api/books/${brief.id}/stats`);
              if (!res.ok) return null;
              const stats = readStatsObject(await res.json());
              if (stats === null) return null;
              return {
                id: brief.id,
                title: brief.title,
                chapterCount: num(stats.chapterCount),
                doneChapterCount: num(stats.doneChapterCount),
                totalWords: num(stats.totalWords),
                outlineCount: num(stats.outlineCount),
                bibleCount: num(stats.bibleCount),
              };
            } catch {
              return null;
            }
          }),
        );
        const rows = results.filter((row): row is BookRow => row !== null);
        rows.sort((a, b) => b.totalWords - a.totalWords);
        setBookRows(rows);
      }

      setError(null);
    } catch {
      setError('加载统计数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // 概览卡：今日字数 / 日目标，百分比封顶 100% 且不出现除零。
  const goalPercent =
    goal > 0 ? Math.min(100, Math.max(0, Math.round((todayWords / goal) * 100))) : 0;
  const chartMax = days.reduce((max, d) => Math.max(max, d.words), 0);
  const compareMax = bookRows.reduce((max, row) => Math.max(max, row.totalWords), 0);

  return (
    <>
      <section className="card">
        <div className="toolbar">
          <div>
            <h1>写作统计</h1>
            <p className="muted">概览、近 14 天节奏、作品对比与本月小结，全部来自本地写作记录。</p>
          </div>
          <Link className="btn btn-ghost" href="/">
            返回书架
          </Link>
        </div>
        {error !== null ? <p className="muted">{error}</p> : null}
        {loading ? <p className="muted">加载中…</p> : null}

        <section className="stats-section">
          <h2>概览</h2>
          <div className="stats-grid">
            <div className="stats-card">
              <span className="stats-card-label">作品数</span>
              <span className="stats-card-value">
                {overview === null ? '—' : fmt(overview.bookCount)}
              </span>
              <span className="stats-card-sub">本地书架中的作品</span>
            </div>
            <div className="stats-card">
              <span className="stats-card-label">章节总数</span>
              <span className="stats-card-value">
                {overview === null ? '—' : fmt(overview.chapterCount)}
              </span>
              <span className="stats-card-sub">全部作品累计章节</span>
            </div>
            <div className="stats-card">
              <span className="stats-card-label">总字数</span>
              <span className="stats-card-value">
                {overview === null ? '—' : fmt(overview.totalWords)}
              </span>
              <span className="stats-card-sub">全部章节字数之和</span>
            </div>
            <div className="stats-card">
              <span className="stats-card-label">今日字数 / 日目标</span>
              <span className="stats-card-value">
                {fmt(todayWords)} / {fmt(goal)}
              </span>
              <div
                className="stats-progress"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={goalPercent}
                aria-label="今日字数占每日目标的比例"
              >
                <div className="stats-progress-fill" style={{ width: `${goalPercent}%` }} />
              </div>
              <span className="stats-card-sub">
                {goal > 0
                  ? `已完成 ${goalPercent}%（${fmt(todayWords)} / ${fmt(goal)} 字）`
                  : `未设置日目标，今日已写 ${fmt(todayWords)} 字`}
              </span>
            </div>
          </div>
        </section>

        <section className="stats-section">
          <h2>近 14 天</h2>
          {chartMax === 0 ? (
            <p className="stats-empty">暂无写作记录</p>
          ) : (
            <div className="stats-chart" role="img" aria-label="近 14 天每日字数柱状图">
              {days.map((day, index) => {
                const isToday = index === days.length - 1;
                const isPeak = day.words === chartMax;
                const heightPercent =
                  chartMax > 0 ? Math.max(2, Math.round((day.words / chartMax) * 100)) : 0;
                return (
                  <div className="stats-chart-col" key={day.date}>
                    <span className="stats-chart-value">{isPeak ? fmt(day.words) : '\u00a0'}</span>
                    <div className="stats-chart-track">
                      <div
                        className={`stats-chart-bar${isToday ? ' is-today' : ''}`}
                        style={{ height: `${heightPercent}%` }}
                        title={`${day.date} · ${fmt(day.words)} 字`}
                      />
                    </div>
                    <span className={`stats-chart-label${isToday ? ' is-today' : ''}`}>
                      {day.date.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="stats-section">
          <h2>作品对比</h2>
          {bookCount === 0 ? (
            <p className="stats-empty">
              还没有作品，<Link href="/">新建书籍</Link>
            </p>
          ) : bookRows.length === 0 ? (
            <p className="stats-empty">作品统计加载失败，可稍后重试</p>
          ) : (
            <div className="stats-compare">
              {bookRows.map((row) => (
                <div className="stats-compare-row" key={row.id}>
                  <div className="stats-compare-head">
                    <span className="stats-compare-title">{row.title}</span>
                    <span className="stats-compare-meta">
                      定稿 {fmt(row.doneChapterCount)} / {fmt(row.chapterCount)} · 章节 {fmt(row.chapterCount)} · 总字数 {fmt(row.totalWords)} · 大纲{' '}
                      {fmt(row.outlineCount)} · 设定 {fmt(row.bibleCount)}
                    </span>
                  </div>
                  <div className="stats-compare-track">
                    <div
                      className="stats-compare-fill"
                      style={{
                        width: `${
                          compareMax > 0 ? Math.max(2, Math.round((row.totalWords / compareMax) * 100)) : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="stats-section">
          <h2>本月小结{month !== null && month.month !== '' ? `（${month.month}）` : ''}</h2>
          <div className="stats-month">
            <div className="stats-card">
              <span className="stats-card-label">本月累计字数</span>
              <span className="stats-card-value">{month === null ? '—' : fmt(month.total)}</span>
            </div>
            <div className="stats-card">
              <span className="stats-card-label">活跃天数</span>
              <span className="stats-card-value">{month === null ? '—' : fmt(month.activeDays)}</span>
            </div>
            <div className="stats-card">
              <span className="stats-card-label">最佳日</span>
              <span className="stats-card-value">
                {month === null || month.bestDay === null
                  ? '暂无'
                  : fmt(month.bestDay.words)}
              </span>
              <span className="stats-card-sub">
                {month !== null && month.bestDay !== null ? month.bestDay.date : '本月还没有记录'}
              </span>
            </div>
            <div className="stats-card">
              <span className="stats-card-label">连续写作天数</span>
              <span className="stats-card-value">{fmt(streak)}</span>
              <span className="stats-card-sub">从今天往前连续有字数的天数</span>
            </div>
          </div>
        </section>
      </section>
    </>
  );
}
