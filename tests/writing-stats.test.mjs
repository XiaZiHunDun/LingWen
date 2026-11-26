import assert from 'node:assert/strict';
import { test } from 'node:test';

import { closeDb, getDb, initDb } from '../src/lib/db.js';
import {
  dailyWordCounts,
  getDailyGoal,
  recordWritingDelta,
  setDailyGoal,
} from '../src/lib/repo.js';

/**
 * 与 tests/db.test.mjs 一致：每个用例先 closeDb() 再开一个全新的 ':memory:' 库，
 * 用例结束后释放，全程不触碰磁盘文件。
 *
 * @param {import('node:test').TestContext} t
 */
function freshDb(t) {
  closeDb();
  initDb(':memory:');
  t.after(() => closeDb());
}

/** writing_sessions 当前行数。 */
function sessionCount() {
  return getDb().prepare('SELECT COUNT(*) AS n FROM writing_sessions').get().n;
}

test('recordWritingDelta：非正整数一律忽略且不写库，正常整数写入返回 id', (t) => {
  freshDb(t);

  for (const bad of [0, -0, 1.5, -2.5, Number.NaN, Number.POSITIVE_INFINITY, 'abc', null]) {
    const res = recordWritingDelta({ bookId: null, chapterId: null, deltaWords: bad });
    assert.deepEqual(res, { id: null }, `deltaWords=${String(bad)} 应被忽略`);
  }
  assert.equal(sessionCount(), 0, '被忽略的增量不应写库');

  const ok = recordWritingDelta({ bookId: null, chapterId: null, deltaWords: 12 });
  assert.equal(typeof ok.id, 'number', '正常整数应返回插入行 id');
  assert.ok(ok.id > 0);
  assert.equal(sessionCount(), 1);

  const neg = recordWritingDelta({ bookId: null, chapterId: null, deltaWords: -7 });
  assert.equal(typeof neg.id, 'number', '非 0 负整数同样写入（表内保留负值）');
  assert.equal(sessionCount(), 2);
});

test('dailyWordCounts：跨天补 0、日期升序、净负值当天为 0', (t) => {
  freshDb(t);

  recordWritingDelta({ bookId: null, chapterId: null, deltaWords: 500 });
  // 同一天再净删超过新增，聚合为负 → 展示口径应为 0。
  recordWritingDelta({ bookId: null, chapterId: null, deltaWords: -830 });

  const list = dailyWordCounts(3);
  assert.equal(list.length, 3, '长度应等于 days');
  assert.equal(list[list.length - 1].words, 0, '当天净负值应 clamp 为 0');

  const dates = list.map((d) => d.date);
  assert.deepEqual(dates, [...dates].sort(), '日期应升序');
  for (const day of list) {
    assert.match(day.date, /^\d{4}-\d{2}-\d{2}$/);
    assert.ok(day.words >= 0, `每日字数不应为负：${day.date} => ${day.words}`);
  }
  // 空白日期补 0（前两天空数据）。
  assert.equal(list[0].words, 0);
  assert.equal(list[1].words, 0);

  // 净正值的当天应正常呈现正数。
  freshDb(t);
  recordWritingDelta({ bookId: null, chapterId: null, deltaWords: 500 });
  recordWritingDelta({ bookId: null, chapterId: null, deltaWords: -200 });
  const positive = dailyWordCounts(2);
  assert.equal(positive.length, 2);
  assert.equal(positive[1].words, 300);
  assert.equal(positive[0].words, 0, '无数据日期补 0');
});

test('setDailyGoal：1 与 20000 合法，0 与 20001 抛 RangeError', (t) => {
  freshDb(t);

  assert.equal(setDailyGoal(1), 1);
  assert.equal(getDailyGoal(), 1);

  assert.equal(setDailyGoal(20000), 20000);
  assert.equal(getDailyGoal(), 20000);

  assert.throws(() => setDailyGoal(0), RangeError);
  assert.throws(() => setDailyGoal(20001), RangeError);
  assert.throws(() => setDailyGoal(12.5), RangeError);
  assert.equal(getDailyGoal(), 20000, '非法写入不应改变已保存的目标');
});
