/**
 * 写作统计 CSV 导出相关的纯函数（无 IO、无 DB 依赖，便于单测）。
 *
 * 口径说明：本模块不重新计算字数。CSV 里的「字数」直接来自
 * repo.dailyWordCounts()（净字数 = writing_sessions.delta_words 按本地日期聚合，
 * 全天净删（负值）按 0 展示），与 /stats 页面展示的数字完全一致；
 * 这里只负责补零、排序、取值校验与 CSV 字段转义。
 */

/** 允许的最小天数。 */
export const MIN_DAYS = 1;
/** 允许的最大天数（与 repo.dailyWordCounts 的上限一致）。 */
export const MAX_DAYS = 365;
/** 未传 days 时的默认窗口。 */
export const DEFAULT_DAYS = 30;

/** UTF-8 BOM：让 Excel 正确识别中文表头。 */
export const UTF8_BOM = '\uFEFF';
/** CSV 表头。 */
export const CSV_HEADER = '日期,字数';
/** 行分隔符遵循 RFC 4180 的 CRLF。 */
const CRLF = '\r\n';

/** 形如 YYYY-MM-DD 的日期串。 */
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
/** 纯整数串（允许负号，用于把越界输入判为非法）。 */
const INTEGER_PATTERN = /^-?\d+$/;

/**
 * 校验 days 查询参数。
 *
 * 规则：未提供（null/undefined/空白）→ 默认 30；只有 1–365 的整数才合法；
 * 非数字（含小数、科学计数法以外的乱码）或越界一律返回 null，交给路由回 400。
 *
 * @param {unknown} raw 原始查询参数
 * @returns {number | null} 合法天数，或 null（非法）
 */
export function parseDaysParam(raw) {
  if (raw === null || raw === undefined) return DEFAULT_DAYS;
  const text = typeof raw === 'string' ? raw.trim() : String(raw);
  if (text === '') return DEFAULT_DAYS;
  if (!INTEGER_PATTERN.test(text)) return null;
  const value = Number(text);
  if (!Number.isInteger(value)) return null;
  if (value < MIN_DAYS || value > MAX_DAYS) return null;
  return value;
}

/**
 * 按 RFC 4180 转义单个 CSV 字段：含逗号、双引号或换行时整体加双引号，
 * 内部双引号翻倍。
 *
 * @param {unknown} value 待输出值
 * @returns {string} 可直接拼接的字段文本
 */
export function escapeCsvField(value) {
  const text = value === null || value === undefined ? '' : String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

/**
 * 本地时区下把 Date 格式化成 YYYY-MM-DD。
 *
 * @param {Date} date
 * @returns {string}
 */
function formatDateKey(date) {
  const year = String(date.getFullYear()).padStart(4, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 把 YYYY-MM-DD 解析为本地零点 Date；非法（格式不符 / 不存在的日期）返回 null。
 *
 * @param {unknown} key
 * @returns {Date | null}
 */
function parseDateKey(key) {
  if (typeof key !== 'string') return null;
  const text = key.trim();
  if (!DATE_PATTERN.test(text)) return null;
  const parts = text.split('-').map(Number);
  const date = new Date(parts[0], parts[1] - 1, parts[2]);
  if (Number.isNaN(date.getTime())) return null;
  // 排除 2024-02-31 这类溢出到下个月的伪日期。
  if (
    date.getFullYear() !== parts[0] ||
    date.getMonth() !== parts[1] - 1 ||
    date.getDate() !== parts[2]
  ) {
    return null;
  }
  return date;
}

/**
 * 以本地零点为基准加减天数（避免跨夏令时的小时漂移）。
 *
 * @param {Date} date
 * @param {number} delta
 * @returns {Date}
 */
function addDays(date, delta) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + delta);
}

/**
 * 字数取整并清洗脏值：非有限数（undefined/NaN/Infinity/字符串垃圾）按 0。
 * 负数原样保留由调用方决定口径（仓库里 dailyWordCounts 已把净删按 0 输出）。
 *
 * @param {unknown} value
 * @returns {number}
 */
function normalizeWords(value) {
  const n = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.trunc(n);
}

/**
 * 生成最近 N 天的每日字数 CSV。
 *
 * 行为：
 * - 以数据中最新的一天为窗口右端（无数据时取今天），向左取 days 天；
 * - 日期升序；窗口内没有记录的日子补 0 行，数据行数严格等于 days；
 * - 输出以 UTF-8 BOM 开头，表头为「日期,字数」；
 * - 非法日期行被忽略，重复日期以最后一次出现为准。
 *
 * @param {unknown} dailyRows [{ date: 'YYYY-MM-DD', words: number }, ...]
 * @param {unknown} days 1–365 的整数（缺省 30）
 * @returns {string} 带 BOM 的 CSV 文本
 * @throws {RangeError} days 非法时抛出（路由需先校验）
 */
export function buildDailyStatsCsv(dailyRows, days) {
  const span = parseDaysParam(days);
  if (span === null) {
    throw new RangeError(`days 必须是 ${MIN_DAYS}-${MAX_DAYS} 的整数`);
  }

  /** @type {Map<string, number>} */
  const byDate = new Map();
  /** @type {Date | null} */
  let latest = null;

  if (Array.isArray(dailyRows)) {
    for (const row of dailyRows) {
      if (row === null || typeof row !== 'object') continue;
      const record = /** @type {Record<string, unknown>} */ (row);
      const date = parseDateKey(record.date);
      if (date === null) continue;
      byDate.set(formatDateKey(date), normalizeWords(record.words));
      if (latest === null || date.getTime() > latest.getTime()) latest = date;
    }
  }

  const end = latest === null ? new Date() : latest;
  /** @type {string[]} */
  const lines = [CSV_HEADER];
  for (let offset = span - 1; offset >= 0; offset -= 1) {
    const key = formatDateKey(addDays(end, -offset));
    // gap 补 0；已有值为 0 时同样输出 0，保证行数严格等于 days。
    const words = byDate.get(key) ?? 0;
    lines.push(`${escapeCsvField(key)},${escapeCsvField(words)}`);
  }

  return `${UTF8_BOM}${lines.join(CRLF)}${CRLF}`;
}
