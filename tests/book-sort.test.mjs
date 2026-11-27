import assert from 'node:assert/strict';
import { test } from 'node:test';

import { closeDb, initDb } from '../src/lib/db.js';
import {
  BOOK_SORTS,
  DEFAULT_BOOK_SORT,
  createBook,
  createChapter,
  listBooks,
  updateChapter,
} from '../src/lib/repo.js';

/**
 * 沿用 tests/db.test.mjs / book-progress.test.mjs 的写法：db.js 是单例连接，
 * 先 closeDb() 释放旧连接，再打开全新的 :memory: 库；用例结束通过 t.after 清理。
 * 全程不落盘，可重复运行。
 *
 * @param {import('node:test').TestContext} t
 * @returns {import('better-sqlite3').Database}
 */
function freshDb(t) {
  closeDb();
  const db = initDb(':memory:');
  t.after(() => closeDb());
  return db;
}

/** 直接执行 SQL（测试里用来精确控制 created_at / updated_at）。 */
function run(db, sql, ...params) {
  db.prepare(sql).run(...params);
}

/** 从 listBooks() 结果里按 id 取回一本书。 */
function findBook(books, id) {
  return books.find((book) => Number(book.id) === Number(id));
}

/** 取出排序结果里的书名序列，便于断言顺序。 */
function titles(books) {
  return books.map((book) => String(book.title));
}

test('四本书的初始数据：字数、最近编辑时间各不相同', (t) => {
  const db = freshDb(t);

  const alpha = createBook({ title: 'Alpha' }); // 2 章，共 300 字，最新编辑最早
  const beta = createBook({ title: 'beta' }); // 1 章，1500 字，最新编辑最晚
  const gamma = createBook({ title: 'Gamma' }); // 无章节，0 字
  const delta = createBook({ title: 'Delta' }); // 2 章，共 700 字

  const a1 = createChapter({ bookId: Number(alpha.id), seq: 1, title: 'A1' });
  const a2 = createChapter({ bookId: Number(alpha.id), seq: 2, title: 'A2' });
  updateChapter(Number(a1.id), { wordCount: 100 });
  updateChapter(Number(a2.id), { wordCount: 200 });

  const b1 = createChapter({ bookId: Number(beta.id), seq: 1, title: 'B1' });
  updateChapter(Number(b1.id), { wordCount: 1500 });

  const d1 = createChapter({ bookId: Number(delta.id), seq: 1, title: 'D1' });
  const d2 = createChapter({ bookId: Number(delta.id), seq: 2, title: 'D2' });
  updateChapter(Number(d1.id), { wordCount: 300 });
  updateChapter(Number(d2.id), { wordCount: 400 });

  // 精确控制时间戳：书的创建时间、章节的更新时间。
  run(db, 'UPDATE books SET created_at = ? WHERE id = ?', '2024-01-01 00:00:00', alpha.id);
  run(db, 'UPDATE books SET created_at = ? WHERE id = ?', '2024-03-01 00:00:00', beta.id);
  run(db, 'UPDATE books SET created_at = ? WHERE id = ?', '2024-02-01 00:00:00', gamma.id);
  run(db, 'UPDATE books SET created_at = ? WHERE id = ?', '2024-04-01 00:00:00', delta.id);

  run(db, "UPDATE chapters SET updated_at = '2024-05-01 10:00:00' WHERE id = ?", a1.id);
  run(db, "UPDATE chapters SET updated_at = '2024-05-02 10:00:00' WHERE id = ?", a2.id);
  run(db, "UPDATE chapters SET updated_at = '2024-05-04 10:00:00' WHERE id = ?", b1.id);
  run(db, "UPDATE chapters SET updated_at = '2024-05-02 09:00:00' WHERE id = ?", d1.id);
  run(db, "UPDATE chapters SET updated_at = '2024-05-03 10:00:00' WHERE id = ?", d2.id);
  // 无章节的书的最近编辑时间应回落到 books.updated_at。
  run(db, "UPDATE books SET updated_at = '2024-04-15 08:30:00' WHERE id = ?", gamma.id);

  // 默认排序 = 'updated'（最近编辑 DESC）。
  assert.equal(DEFAULT_BOOK_SORT, 'updated');
  assert.deepEqual(titles(listBooks()), ['beta', 'Delta', 'Alpha', 'Gamma']);
  assert.deepEqual(titles(listBooks({ sort: 'updated' })), ['beta', 'Delta', 'Alpha', 'Gamma']);

  // 'created'：books.created_at DESC。
  assert.deepEqual(titles(listBooks({ sort: 'created' })), ['Delta', 'beta', 'Gamma', 'Alpha']);

  // 'title'：COLLATE NOCASE 升序（大小写不敏感）。
  assert.deepEqual(titles(listBooks({ sort: 'title' })), ['Alpha', 'beta', 'Delta', 'Gamma']);

  // 'words'：wordCount DESC，0 章节/0 字的排在最后。
  assert.deepEqual(titles(listBooks({ sort: 'words' })), ['beta', 'Delta', 'Alpha', 'Gamma']);

  // 白名单导出：与实现保持一致。
  assert.deepEqual([...BOOK_SORTS], ['updated', 'created', 'title', 'words']);

  // 未知排序值抛错（路由层会先校验并返回 400）。
  assert.throws(() => listBooks({ sort: 'bogus' }), /非法的排序方式/);
});

test('聚合 wordCount / lastEditedAt：无章节的书为 0 与 books.updated_at', (t) => {
  const db = freshDb(t);

  const withChapters = createBook({ title: '有章节' });
  const empty = createBook({ title: '空书' });

  const c1 = createChapter({ bookId: Number(withChapters.id), seq: 1, title: '第一章' });
  const c2 = createChapter({ bookId: Number(withChapters.id), seq: 2, title: '第二章' });
  updateChapter(Number(c1.id), { wordCount: 120 });
  updateChapter(Number(c2.id), { wordCount: 80 });

  run(db, "UPDATE chapters SET updated_at = '2024-06-01 12:00:00' WHERE id = ?", c1.id);
  run(db, "UPDATE chapters SET updated_at = '2024-06-05 20:15:00' WHERE id = ?", c2.id);
  run(db, 'UPDATE books SET updated_at = ? WHERE id = ?', '2024-06-09 00:00:00', empty.id);

  const books = listBooks({ sort: 'words' });
  assert.equal(books.length, 2, 'JOIN 不应把书放大成多行');

  const rich = findBook(books, Number(withChapters.id));
  assert.ok(rich);
  assert.equal(rich.wordCount, 200);
  // 取章节 updated_at 的最大值，而不是书自身的 updated_at。
  assert.equal(rich.lastEditedAt, '2024-06-05 20:15:00');
  // 原有聚合字段不受影响。
  assert.equal(rich.chapterCount, 2);
  assert.equal(rich.doneChapterCount, 0);

  const bare = findBook(books, Number(empty.id));
  assert.ok(bare, '未找到无章节的书');
  assert.equal(bare.wordCount, 0);
  assert.equal(bare.chapterCount, 0);
  assert.equal(bare.doneChapterCount, 0);
  // 无章节时回落到 books.updated_at。
  assert.equal(bare.lastEditedAt, '2024-06-09 00:00:00');
});

test('排序在同值时用稳定的次级键（id）兜底', (t) => {
  freshDb(t);

  // 两本无章节的书：wordCount 都是 0，'words' 排序按 b.id ASC。
  const first = createBook({ title: '同字一' });
  const second = createBook({ title: '同字二' });

  assert.deepEqual(titles(listBooks({ sort: 'words' })), ['同字一', '同字二']);
  // 书名排序同样以 b.id ASC 兜底。
  assert.deepEqual(titles(listBooks({ sort: 'title' })), ['同字一', '同字二']);
  assert.equal(Number(first.id) < Number(second.id), true);
});
