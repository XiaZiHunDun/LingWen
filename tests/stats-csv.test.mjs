import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  CSV_HEADER,
  DEFAULT_DAYS,
  MAX_DAYS,
  MIN_DAYS,
  buildDailyStatsCsv,
  escapeCsvField,
  parseDaysParam,
} from '../src/lib/stats-csv.js';

/** 去掉 BOM、按 CRLF 切行并丢掉尾部空行。 */
function csvLines(csv) {
  assert.ok(csv.startsWith('\uFEFF'), 'CSV 必须以 UTF-8 BOM 开头');
  return csv.slice(1).split('\r\n').filter((line) => line !== '');
}

/** 从 2024-01-03 往前（含）推 n 天，用于构造期望日期。 */
function dateBack(baseKey, days) {
  const parts = baseKey.split('-').map(Number);
  const end = new Date(parts[0], parts[1] - 1, parts[2]);
  const out = [];
  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const d = new Date(end.getFullYear(), end.getMonth(), end.getDate() - offset);
    const y = String(d.getFullYear()).padStart(4, '0');
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    out.push(`${y}-${m}-${day}`);
  }
  return out;
}

test('buildDailyStatsCsv：行数严格等于 days、日期升序、缺日补 0、BOM 与表头', () => {
  const rows = [
    { date: '2024-01-03', words: 300 },
    { date: '2024-01-01', words: 100 },
  ];
  const lines = csvLines(buildDailyStatsCsv(rows, 5));

  assert.equal(lines[0], CSV_HEADER, '表头应为「日期,字数」');
  assert.equal(lines[0], '日期,字数');

  const dataLines = lines.slice(1);
  assert.equal(dataLines.length, 5, '数据行数必须严格等于 days');

  const expectedDates = dateBack('2024-01-03', 5);
  assert.deepEqual(
    dataLines.map((line) => line.split(',')[0]),
    expectedDates,
    '日期应升序且以最新数据日为右端',
  );
  for (let i = 1; i < expectedDates.length; i += 1) {
    assert.ok(expectedDates[i - 1] < expectedDates[i], '日期必须严格递增');
  }

  // 2024-01-02 / 2023-12-30 / 2023-12-31 无记录 → 0；有记录的两天取原值。
  assert.deepEqual(dataLines, [
    '2023-12-30,0',
    '2023-12-31,0',
    '2024-01-01,100',
    '2024-01-02,0',
    '2024-01-03,300',
  ]);
});

test('buildDailyStatsCsv：空数据也补齐 days 行、全部为 0，且不抛错', () => {
  for (const days of [1, 30, MAX_DAYS]) {
    const lines = csvLines(buildDailyStatsCsv([], days));
    assert.equal(lines[0], CSV_HEADER);
    const dataLines = lines.slice(1);
    assert.equal(dataLines.length, days, `days=${days} 时数据行数应等于 days`);
    for (const line of dataLines) {
      assert.match(line, /^\d{4}-\d{2}-\d{2},0$/, `无记录日期应补 0 行：${line}`);
    }
  }
});

test('buildDailyStatsCsv：行数多于 days 时只保留最近 days 天，脏值/非法日期被忽略', () => {
  const rows = [
    { date: '2024-01-01', words: 1 },
    { date: '2024-01-02', words: 2 },
    { date: '2024-01-03', words: Number.NaN },
    { date: '2024-01-04', words: '60' },
    { date: '2024-02-31', words: 999 }, // 不存在的日期
    { date: 'bad-date', words: 999 },
    null,
    'oops',
  ];
  const dataLines = csvLines(buildDailyStatsCsv(rows, 3)).slice(1);
  assert.deepEqual(dataLines, ['2024-01-02,2', '2024-01-03,0', '2024-01-04,60']);
});

test('buildDailyStatsCsv：days 非法时抛 RangeError', () => {
  assert.throws(() => buildDailyStatsCsv([], 0), RangeError);
  assert.throws(() => buildDailyStatsCsv([], 366), RangeError);
  assert.throws(() => buildDailyStatsCsv([], 'abc'), RangeError);
  assert.throws(() => buildDailyStatsCsv([], 3.5), RangeError);
});

test('escapeCsvField：逗号/双引号/换行按 CSV 规范转义', () => {
  assert.equal(escapeCsvField('普通文本'), '普通文本');
  assert.equal(escapeCsvField(123), '123');
  assert.equal(escapeCsvField(null), '');
  assert.equal(escapeCsvField(undefined), '');
  assert.equal(escapeCsvField('a,b'), '"a,b"');
  assert.equal(escapeCsvField('say "hi"'), '"say ""hi"""');
  assert.equal(escapeCsvField('line1\nline2'), '"line1\nline2"');
  assert.equal(escapeCsvField('line1\r\nline2'), '"line1\r\nline2"');
  assert.equal(escapeCsvField('a,"b"'), '"a,""b"""');
});

test('parseDaysParam：默认 30、边界 1/365 合法、越界与非数字非法', () => {
  assert.equal(DEFAULT_DAYS, 30);
  assert.equal(MIN_DAYS, 1);
  assert.equal(MAX_DAYS, 365);

  // 默认值：参数缺失或空白。
  assert.equal(parseDaysParam(null), 30);
  assert.equal(parseDaysParam(undefined), 30);
  assert.equal(parseDaysParam(''), 30);
  assert.equal(parseDaysParam('   '), 30);

  // 合法整数（字符串与数字都接受）。
  assert.equal(parseDaysParam('30'), 30);
  assert.equal(parseDaysParam(30), 30);
  assert.equal(parseDaysParam('1'), 1);
  assert.equal(parseDaysParam('365'), 365);
  assert.equal(parseDaysParam(' 14 '), 14);

  // 越界与非法格式。
  for (const bad of ['0', '366', '-1', '1.5', '30abc', 'abc', 'NaN', 'Infinity', 0, 366, 1.5, -7, Number.NaN]) {
    assert.equal(parseDaysParam(bad), null, `days=${String(bad)} 应判为非法`);
  }
});
