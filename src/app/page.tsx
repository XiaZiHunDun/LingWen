'use client';

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from 'react';
import { useRouter } from 'next/navigation';

/** 全局搜索结果条目（与 /api/search 返回结构一致）。 */
type SearchType = 'chapter' | 'outline' | 'bible';

interface SearchItem {
  bookId: number;
  bookTitle: string;
  type: SearchType;
  id: number;
  title: string;
  snippet: string;
}

/** 结果类型 → 中文标签。 */
const SEARCH_TYPE_LABELS: Record<SearchType, string> = {
  chapter: '章节',
  outline: '大纲',
  bible: '设定',
};

/** 从任意 JSON 值里安全取出搜索结果数组。 */
function readSearchItems(payload: unknown): SearchItem[] {
  if (payload === null || typeof payload !== 'object' || !('items' in payload)) return [];
  const raw = (payload as { items?: unknown }).items;
  if (!Array.isArray(raw)) return [];
  const items: SearchItem[] = [];
  for (const entry of raw) {
    if (entry === null || typeof entry !== 'object') continue;
    const row = entry as Record<string, unknown>;
    const type = row.type;
    if (type !== 'chapter' && type !== 'outline' && type !== 'bible') continue;
    items.push({
      bookId: Number(row.bookId),
      bookTitle: typeof row.bookTitle === 'string' ? row.bookTitle : '',
      type,
      id: Number(row.id),
      title: typeof row.title === 'string' ? row.title : '',
      snippet: typeof row.snippet === 'string' ? row.snippet : '',
    });
  }
  return items;
}

/** 后端返回的书籍精简结构。 */
interface Book {
  id: number;
  title: string;
  genre: string | null;
  summary: string | null;
  style: string | null;
  updatedAt: string | null;
}

/** 全站统计结构。 */
interface Stats {
  bookCount: number;
  chapterCount: number;
  totalWords: number;
  outlineCount: number;
  bibleCount: number;
}

/** 从任意 JSON 值里安全取出错误文案。 */
function readError(payload: unknown, fallback: string): string {
  if (payload !== null && typeof payload === 'object' && 'error' in payload) {
    const value = (payload as { error?: unknown }).error;
    if (typeof value === 'string' && value.trim() !== '') return value;
  }
  return fallback;
}

/** 从任意 JSON 值里安全取出统计数字，缺失或类型不符时返回 null。 */
function readStats(payload: unknown): Stats | null {
  if (payload === null || typeof payload !== 'object' || !('stats' in payload)) return null;
  const raw = (payload as { stats?: unknown }).stats;
  if (raw === null || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const { bookCount, chapterCount, totalWords, outlineCount, bibleCount } = source;
  if (
    typeof bookCount !== 'number' ||
    typeof chapterCount !== 'number' ||
    typeof totalWords !== 'number' ||
    typeof outlineCount !== 'number' ||
    typeof bibleCount !== 'number'
  ) {
    return null;
  }
  return { bookCount, chapterCount, totalWords, outlineCount, bibleCount };
}

/** 把 YYYY-MM 平移 offset 个月，返回同格式的月份字符串。 */
function shiftMonthKey(month: string, offset: number): string {
  const [yearText, monthText] = month.split('-');
  const base = new Date(Number(yearText), Number(monthText) - 1 + offset, 1);
  return `${base.getFullYear()}-${String(base.getMonth() + 1).padStart(2, '0')}`;
}

export default function BookshelfPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

  // 写作日历：近 14 天每日字数、今日字数、每日目标。
  const [dailyDays, setDailyDays] = useState<Array<{ date: string; words: number }>>([]);
  const [todayWords, setTodayWords] = useState(0);
  const [dailyGoal, setDailyGoalValue] = useState(1000);
  // 连续写作天数使用 90 天窗口（dailyDays 只保留最近 14 天用于柱图）。
  const [streakDays, setStreakDays] = useState<Array<{ date: string; words: number }>>([]);

  // 月视图：是否展开、当前查看月份（YYYY-MM）、当月每日字数与汇总。
  const [monthOpen, setMonthOpen] = useState(false);
  const [month, setMonth] = useState<string>(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [monthDays, setMonthDays] = useState<Array<{ date: string; words: number }>>([]);
  const [monthSummary, setMonthSummary] = useState<{
    total: number;
    activeDays: number;
    bestDay: { date: string; words: number } | null;
  } | null>(null);

  const loadDaily = useCallback(async (): Promise<void> => {
    try {
      const res = await fetch('/api/stats/daily?days=90');
      if (!res.ok) return;
      const data: unknown = await res.json();
      if (data === null || typeof data !== 'object') return;
      const source = data as Record<string, unknown>;

      const parsed: Array<{ date: string; words: number }> = [];
      if (Array.isArray(source.days)) {
        for (const item of source.days) {
          if (item === null || typeof item !== 'object') continue;
          const row = item as Record<string, unknown>;
          const date = typeof row.date === 'string' ? row.date : '';
          const words =
            typeof row.words === 'number' && Number.isFinite(row.words) ? row.words : 0;
          if (date !== '') parsed.push({ date, words });
        }
      }
      setDailyDays(parsed.slice(-14));
      setStreakDays(parsed);
      setTodayWords(
        typeof source.todayWords === 'number' && Number.isFinite(source.todayWords)
          ? source.todayWords
          : 0,
      );
      setDailyGoalValue(
        typeof source.goal === 'number' && Number.isFinite(source.goal) ? source.goal : 1000,
      );
    } catch {
      // 写作日历属于增强信息，加载失败不影响书架主体。
    }
  }, []);

  useEffect(() => {
    void loadDaily();
  }, [loadDaily]);

  /** 拉取指定月份的每日字数（GET /api/stats/month?month=YYYY-MM）。 */
  const loadMonth = useCallback(async (target: string): Promise<void> => {
    try {
      const res = await fetch(`/api/stats/month?month=${encodeURIComponent(target)}`);
      if (!res.ok) {
        setMonthDays([]);
        setMonthSummary(null);
        return;
      }
      const data: unknown = await res.json();
      if (data === null || typeof data !== 'object') return;
      const source = data as Record<string, unknown>;

      const parsed: Array<{ date: string; words: number }> = [];
      if (Array.isArray(source.days)) {
        for (const item of source.days) {
          if (item === null || typeof item !== 'object') continue;
          const row = item as Record<string, unknown>;
          const date = typeof row.date === 'string' ? row.date : '';
          const words =
            typeof row.words === 'number' && Number.isFinite(row.words) ? row.words : 0;
          if (date !== '') parsed.push({ date, words });
        }
      }

      let bestDay: { date: string; words: number } | null = null;
      if (source.bestDay !== null && typeof source.bestDay === 'object') {
        const row = source.bestDay as Record<string, unknown>;
        const date = typeof row.date === 'string' ? row.date : '';
        const words = typeof row.words === 'number' && Number.isFinite(row.words) ? row.words : 0;
        if (date !== '') bestDay = { date, words };
      }

      setMonthDays(parsed);
      setMonthSummary({
        total: typeof source.total === 'number' && Number.isFinite(source.total) ? source.total : 0,
        activeDays:
          typeof source.activeDays === 'number' && Number.isFinite(source.activeDays)
            ? source.activeDays
            : 0,
        bestDay,
      });
    } catch {
      setMonthDays([]);
      setMonthSummary(null);
    }
  }, []);

  // 只有展开月视图时才请求当月数据，避免多余请求。
  useEffect(() => {
    if (!monthOpen) return;
    void loadMonth(month);
  }, [monthOpen, month, loadMonth]);

  // 点击「今日 / 目标」设置每日目标，成功后重新拉取日历数据。
  const handleSetGoal = useCallback(async (): Promise<void> => {
    const input = window.prompt('设置每日目标字数（1 - 20000）', String(dailyGoal));
    if (input === null) return;
    const goal = Number(input.trim());
    if (!Number.isInteger(goal) || goal < 1 || goal > 20000) {
      window.alert('请输入 1 - 20000 之间的整数');
      return;
    }
    try {
      const res = await fetch('/api/settings/daily-goal', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal }),
      });
      if (!res.ok) {
        window.alert('设置每日目标失败');
        return;
      }
      await loadDaily();
    } catch {
      window.alert('设置每日目标失败');
    }
  }, [dailyGoal, loadDaily]);

  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('');
  const [summary, setSummary] = useState('');
  const [style, setStyle] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // 导入 JSON 快照：进行中状态、成功提示、隐藏的文件选择框。
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const importInputRef = useRef<HTMLInputElement | null>(null);

  const loadBooks = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const res = await fetch('/api/books');
      const data: unknown = await res.json();
      if (!res.ok) {
        setError(readError(data, '加载作品列表失败'));
        return;
      }
      const list =
        data !== null && typeof data === 'object' && 'books' in data
          ? (data as { books?: unknown }).books
          : undefined;
      setBooks(Array.isArray(list) ? (list as Book[]) : []);
      setError(null);
    } catch {
      setError('加载作品列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBooks();
  }, [loadBooks]);

  useEffect(() => {
    let active = true;
    void (async (): Promise<void> => {
      try {
        const res = await fetch('/api/stats');
        if (!res.ok) {
          if (active) setStats(null);
          return;
        }
        const data: unknown = await res.json();
        if (active) setStats(readStats(data));
      } catch {
        if (active) setStats(null);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const router = useRouter();

  // 全局搜索：输入、结果、请求中、浮层开关、是否已拿到结果。
  const [searchQuery, setSearchQuery] = useState('');
  const [searchItems, setSearchItems] = useState<SearchItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchDone, setSearchDone] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchBoxRef = useRef<HTMLDivElement | null>(null);
  // 键盘导航：高亮下标（-1 表示无高亮）与结果按钮 ref（用于滚动到可视区）。
  const [activeIndex, setActiveIndex] = useState(-1);
  const resultRefs = useRef<Array<HTMLButtonElement | null>>([]);
  // 递增请求序号，丢弃过期响应，避免旧结果覆盖新结果。
  const searchSeqRef = useRef(0);

  useEffect(() => {
    const q = searchQuery.trim();
    if (q === '') {
      searchSeqRef.current += 1;
      setSearchItems([]);
      setSearchLoading(false);
      setSearchDone(false);
      setSearchOpen(false);
      return;
    }
    searchSeqRef.current += 1;
    const seq = searchSeqRef.current;
    setSearchOpen(true);
    setSearchLoading(true);
    const timer = window.setTimeout(() => {
      void (async (): Promise<void> => {
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
          if (searchSeqRef.current !== seq) return;
          if (!res.ok) {
            setSearchItems([]);
            setSearchDone(true);
            return;
          }
          const data: unknown = await res.json();
          if (searchSeqRef.current !== seq) return;
          setSearchItems(readSearchItems(data));
          setSearchDone(true);
        } catch {
          if (searchSeqRef.current !== seq) return;
          setSearchItems([]);
          setSearchDone(true);
        } finally {
          if (searchSeqRef.current === seq) setSearchLoading(false);
        }
      })();
    }, 300);
    return () => {
      window.clearTimeout(timer);
    };
  }, [searchQuery]);

  // 结果变化时重置高亮：有新结果高亮第一项，无结果清除高亮。
  useEffect(() => {
    setActiveIndex(searchItems.length > 0 ? 0 : -1);
  }, [searchItems]);

  // 高亮项变化时滚动到可视区（就近滚动，不跳动整页）。
  useEffect(() => {
    if (activeIndex < 0) return;
    const node = resultRefs.current[activeIndex];
    if (node !== undefined && node !== null) node.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  // Esc 关闭浮层；点击浮层外（不在搜索框容器内）关闭。
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') setSearchOpen(false);
    };
    const onMouseDown = (event: MouseEvent): void => {
      const box = searchBoxRef.current;
      if (box !== null && event.target instanceof Node && box.contains(event.target)) return;
      setSearchOpen(false);
    };
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('mousedown', onMouseDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('mousedown', onMouseDown);
    };
  }, []);

  function handleOpenResult(item: SearchItem): void {
    setSearchOpen(false);
    router.push(
      item.type === 'chapter' ? `/books/${item.bookId}?chapter=${item.id}` : `/books/${item.bookId}`,
    );
  }

  /** 选择 JSON 快照文件后导入：本地先解析校验，再把原文整段提交给导入接口。 */
  async function handleImportFile(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const input = event.target;
    const file = input.files?.[0];
    if (file === undefined || file === null) return;
    setImportMessage(null);
    setImporting(true);
    try {
      const text = await file.text();
      let parsed: unknown;
      try {
        parsed = JSON.parse(text) as unknown;
      } catch (err) {
        setError(`JSON 解析失败：${err instanceof Error ? err.message : String(err)}`);
        return;
      }
      // 导入接口成功时只返回新建书籍 id（{ id }），书名取自快照自身的 book.title。
      let snapshotTitle = '';
      if (parsed !== null && typeof parsed === 'object' && 'book' in parsed) {
        const bookRaw = (parsed as { book?: unknown }).book;
        if (bookRaw !== null && typeof bookRaw === 'object' && 'title' in bookRaw) {
          const raw = (bookRaw as { title?: unknown }).title;
          if (typeof raw === 'string') snapshotTitle = raw.trim();
        }
      }
      const res = await fetch('/api/books/import/json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: text,
      });
      let data: unknown = null;
      try {
        data = (await res.json()) as unknown;
      } catch {
        data = null;
      }
      if (!res.ok) {
        setError(readError(data, '导入失败'));
        return;
      }
      setError(null);
      setImportMessage(snapshotTitle === '' ? '已导入新的作品' : `已导入《${snapshotTitle}》`);
      await loadBooks();
    } catch {
      setError('导入失败');
    } finally {
      setImporting(false);
      // 清空 value，允许重复选择同一个文件。
      input.value = '';
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (title.trim() === '') {
      setError('书名不能为空');
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch('/api/books', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          genre,
          summary,
          style,
        }),
      });
      const data: unknown = await res.json();
      if (!res.ok) {
        setError(readError(data, '新建作品失败'));
        return;
      }
      setTitle('');
      setGenre('');
      setSummary('');
      setStyle('');
      setError(null);
      await loadBooks();
    } catch {
      setError('新建作品失败');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(book: Book): Promise<void> {
    if (!window.confirm(`确定删除《${book.title}》吗？该操作不可撤销。`)) return;
    try {
      const res = await fetch(`/api/books/${book.id}`, { method: 'DELETE' });
      const data: unknown = await res.json();
      if (!res.ok) {
        setError(readError(data, '删除作品失败'));
        return;
      }
      setError(null);
      await loadBooks();
    } catch {
      setError('删除作品失败');
    }
  }

  return (
    <>
      <section className="card">
        <div className="toolbar">
          <div>
            <h1>我的书架</h1>
            <p className="muted">长篇连载从这里开始：新建一本作品，再进入工作台铺大纲、写章节。</p>
          </div>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => router.push('/stats')}
          >
            写作统计
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={importing}
            onClick={() => importInputRef.current?.click()}
          >
            {importing ? '导入中…' : '导入 JSON'}
          </button>
          <input
            type="file"
            accept=".json,application/json"
            ref={importInputRef}
            onChange={(e) => {
              void handleImportFile(e);
            }}
            style={{ display: 'none' }}
          />
        </div>
        {importMessage !== null ? <p className="muted">{importMessage}</p> : null}
        <div className="field" ref={searchBoxRef} style={{ position: 'relative' }}>
          <label htmlFor="global-search">全局搜索</label>
          <input
            id="global-search"
            className="input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => {
              if (searchQuery.trim() !== '') setSearchOpen(true);
            }}
            placeholder="搜索章节标题 / 正文 / 大纲 / 设定…"
            autoComplete="off"
            onKeyDown={(e) => {
              if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (searchItems.length === 0) return;
                setSearchOpen(true);
                setActiveIndex((prev) => (prev + 1) % searchItems.length);
                return;
              }
              if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (searchItems.length === 0) return;
                setSearchOpen(true);
                setActiveIndex((prev) => (prev <= 0 ? searchItems.length - 1 : prev - 1));
                return;
              }
              if (e.key === 'Enter') {
                if (activeIndex >= 0 && activeIndex < searchItems.length) {
                  e.preventDefault();
                  handleOpenResult(searchItems[activeIndex]);
                }
                return;
              }
              if (e.key === 'Escape') {
                e.preventDefault();
                setSearchOpen(false);
              }
            }}
          />
          {searchOpen ? (
            <div
              className="card search-overlay"
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: 4,
                zIndex: 50,
                maxHeight: 360,
                overflowY: 'auto',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.18)',
              }}
            >
              {searchItems.length === 0 ? (
                searchLoading || !searchDone ? (
                  <p className="muted">搜索中…</p>
                ) : (
                  <p className="muted">未找到相关内容</p>
                )
              ) : (
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {searchItems.map((item, index) => (
                    <li key={`${item.type}-${item.id}`}>
                      <button
                        ref={(node) => {
                          resultRefs.current[index] = node;
                        }}
                        type="button"
                        style={{
                          display: 'block',
                          width: '100%',
                          textAlign: 'left',
                          background:
                            activeIndex === index ? 'rgba(59,130,246,0.18)' : 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'inherit',
                          padding: '8px 10px',
                        }}
                        onMouseEnter={() => setActiveIndex(index)}
                        onClick={() => handleOpenResult(item)}
                      >
                        <div>
                          <strong>{item.bookTitle}</strong>
                          {' · '}
                          {SEARCH_TYPE_LABELS[item.type]}
                          {' · '}
                          <span>{item.title}</span>
                        </div>
                        {item.snippet !== '' ? (
                          <p
                            className="muted line-clamp-2"
                            style={{
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden',
                              margin: 0,
                            }}
                          >
                            {item.snippet}
                          </p>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}
        </div>
        {stats !== null ? (
          <p className="muted">
            作品 {stats.bookCount} · 章节 {stats.chapterCount} · 总字数{' '}
            {stats.totalWords.toLocaleString('zh-CN')}
          </p>
        ) : null}
        {(() => {
          const peak = Math.max(dailyGoal, 1, ...dailyDays.map((d) => d.words));
          // 写作日历展示口径：今日字数可能为负（净删），百分比限定在 0..100。
          const percent =
            dailyGoal > 0
              ? Math.min(100, Math.max(0, Math.round((todayWords / dailyGoal) * 100)))
              : 0;
          const goalReached = dailyGoal > 0 && todayWords >= dailyGoal;
          const remaining = Math.max(0, dailyGoal - todayWords);
          // 连续写作天数：今天为 0 则从昨天往前数，遇到 0 字那天即停止。
          const streak = (() => {
            let index = streakDays.length - 1;
            if (index < 0) return 0;
            if (streakDays[index].words <= 0) index -= 1;
            let count = 0;
            while (index >= 0 && streakDays[index].words > 0) {
              count += 1;
              index -= 1;
            }
            return count;
          })();
          // 月视图 7 列网格：按周一为一周起点补齐月初空格。
          const monthLead = monthDays.length > 0 ? (new Date(`${month}-01T00:00:00`).getDay() + 6) % 7 : 0;
          return (
            <div style={{ marginTop: 10 }}>
              <button
                type="button"
                onClick={() => void handleSetGoal()}
                title="点击设置每日目标"
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  font: 'inherit',
                  color: 'inherit',
                  opacity: 0.85,
                }}
              >
                今日 {todayWords.toLocaleString('zh-CN')} / 目标{' '}
                {dailyGoal.toLocaleString('zh-CN')} 字（{percent}%）
              </button>
              <div
                style={{
                  height: 8,
                  marginTop: 6,
                  borderRadius: 999,
                  background: 'rgba(148, 163, 184, 0.35)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${percent}%`,
                    background: todayWords >= dailyGoal ? '#16a34a' : '#2563eb',
                    transition: 'width .3s ease',
                  }}
                />
              </div>
              <p className={goalReached ? 'cal-goal is-done' : 'cal-goal'}>
                {goalReached
                  ? '今日目标已达成'
                  : `还差 ${remaining.toLocaleString('zh-CN')} 字`}
              </p>
              <p className={streak > 0 ? 'cal-streak is-active' : 'cal-streak'}>
                {streak > 0 ? `连续写作 ${streak} 天` : '今天还没动笔'}
              </p>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-end',
                  gap: 3,
                  height: 44,
                  marginTop: 10,
                }}
              >
                {dailyDays.map((day) => (
                  <div
                    key={day.date}
                    title={`${day.date}：${day.words} 字`}
                    style={{
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'flex-end',
                      height: '100%',
                    }}
                  >
                    <div
                      style={{
                        height: `${Math.max(2, Math.round((day.words / peak) * 40))}px`,
                        borderRadius: 2,
                        background: day.words > 0 ? '#60a5fa' : 'rgba(148, 163, 184, 0.35)',
                      }}
                    />
                  </div>
                ))}
              </div>
              <div className="cal-month">
                <div className="cal-month-head">
                  <span className="cal-month-title">{month} 月视图</span>
                  <button
                    type="button"
                    className="btn btn-ghost cal-month-toggle"
                    onClick={() => setMonthOpen((prev) => !prev)}
                  >
                    {monthOpen ? '收起月视图' : '展开月视图'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost cal-month-nav"
                    aria-label="上一月"
                    onClick={() => setMonth((prev) => shiftMonthKey(prev, -1))}
                  >
                    ← 上一月
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost cal-month-nav"
                    aria-label="下一月"
                    onClick={() => setMonth((prev) => shiftMonthKey(prev, 1))}
                  >
                    下一月 →
                  </button>
                </div>
                {monthOpen ? (
                  <>
                    <div className="cal-grid">
                      {['一', '二', '三', '四', '五', '六', '日'].map((label) => (
                        <div key={label} className="cal-weekday">
                          周{label}
                        </div>
                      ))}
                      {Array.from({ length: monthLead }, (_, i) => (
                        <div key={`lead-${i}`} className="cal-cell is-empty" aria-hidden />
                      ))}
                      {monthDays.map((day) => {
                        const level =
                          day.words <= 0 ? 0 : day.words < 500 ? 1 : day.words < 1000 ? 2 : 3;
                        return (
                          <div
                            key={day.date}
                            className={`cal-cell cal-level-${level}`}
                            title={`${day.date}：${day.words.toLocaleString('zh-CN')} 字`}
                          >
                            <span className="cal-day-num">{Number(day.date.slice(-2))}</span>
                            <span className="cal-day-words">
                              {day.words.toLocaleString('zh-CN')}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                    {monthSummary !== null ? (
                      <p className="muted cal-month-sum">
                        本月合计 {monthSummary.total.toLocaleString('zh-CN')} 字 · 写作{' '}
                        {monthSummary.activeDays} 天
                        {monthSummary.bestDay !== null
                          ? ` · 最佳 ${monthSummary.bestDay.date.slice(5)}（${monthSummary.bestDay.words.toLocaleString('zh-CN')} 字）`
                          : ''}
                      </p>
                    ) : null}
                  </>
                ) : null}
              </div>
            </div>
          );
        })()}
      </section>

      <section className="card">
        <h2>新建作品</h2>
        <form onSubmit={handleCreate}>
          <div className="field">
            <label htmlFor="book-title">书名（必填）</label>
            <input
              id="book-title"
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如：长夜将明"
            />
          </div>
          <div className="field">
            <label htmlFor="book-genre">题材</label>
            <input
              id="book-genre"
              className="input"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              placeholder="例如：东方玄幻"
            />
          </div>
          <div className="field">
            <label htmlFor="book-summary">简介</label>
            <textarea
              id="book-summary"
              className="textarea"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="一句话讲清故事的核心冲突"
            />
          </div>
          <div className="field">
            <label htmlFor="book-style">文风</label>
            <input
              id="book-style"
              className="input"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              placeholder="例如：冷峻短句、多对白"
            />
          </div>
          <div className="toolbar">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? '创建中…' : '新建作品'}
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <div className="toolbar">
          <h2>作品列表</h2>
          <span className="muted">共 {books.length} 本</span>
        </div>

        {error !== null ? (
          <p className="form-error">{error}</p>
        ) : null}

        {loading ? (
          <p className="muted">加载中…</p>
        ) : books.length === 0 ? (
          <p className="empty">还没有作品，先新建一本吧</p>
        ) : (
          <div className="book-grid">
            {books.map((book) => (
              <article className="book-card" key={book.id}>
                <div className="toolbar">
                  <h3>{book.title}</h3>
                  <span className="badge">{book.genre ?? '未分类'}</span>
                </div>
                <p className="muted">{book.summary ?? '暂无简介'}</p>
                <p className="muted">更新于 {book.updatedAt ?? '未知'}</p>
                <div className="toolbar">
                  <a className="btn btn-ghost" href={`/books/${book.id}`}>
                    进入工作台
                  </a>
                  <a
                    className="btn btn-ghost"
                    href={`/api/books/${book.id}/export/json`}
                    download
                  >
                    导出 JSON
                  </a>
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => {
                      void handleDelete(book);
                    }}
                  >
                    删除
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <p className="muted" style={{ marginTop: 16, textAlign: 'center', fontSize: 12 }}>
        LingWen v0.1.0
      </p>
    </>
  );
}
