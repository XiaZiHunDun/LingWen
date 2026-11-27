import assert from 'node:assert/strict';
import { test } from 'node:test';

import { closeDb, initDb } from '../src/lib/db.js';
import {
  createBook,
  createChapter,
  listBooks,
  listChapters,
  updateChapter,
} from '../src/lib/repo.js';

/**
 * 沿用 tests/db.test.mjs 里的 freshDb 写法：db.js 是单例连接，initDb(':memory:')
 * 在路径一致时会复用旧连接，所以每个用例先 closeDb() 释放，再打开全新内存库，
 * 用例结束后 t.after(closeDb) 清理。全程不触碰磁盘文件，可重复运行。
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

/** 从 listBooks() 结果里按 id 取回一本书。 */
function findBook(books, id) {
  return books.find((book) => Number(book.id) === Number(id));
}

test('listBooks 返回 chapterCount 与 doneChapterCount（1 章定稿）', (t) => {
  freshDb(t);

  const book = createBook({ title: '定稿进度', genre: '玄幻' });
  const bookId = Number(book.id);

  const first = createChapter({ bookId, seq: 1, title: '第一章' });
  createChapter({ bookId, seq: 2, title: '第二章' });
  updateChapter(Number(first.id), { status: 'final' });

  // 另建一本有章节但都未定稿的书，确认聚合按 book_id 正确分组、不串行。
  const other = createBook({ title: '另一本' });
  createChapter({ bookId: Number(other.id), seq: 1, title: '甲' });

  const books = listBooks();
  assert.equal(books.length, 2, '两本书不应因为 JOIN 被放大成多行');

  const row = findBook(books, bookId);
  assert.ok(row, '未找到刚建的书');
  assert.equal(row.chapterCount, 2);
  assert.equal(row.doneChapterCount, 1);

  // 原有字段（含 mapRow 的 snake_case→camelCase 结果）不能丢。
  assert.equal(row.title, '定稿进度');
  assert.equal(row.genre, '玄幻');
  assert.equal(typeof row.createdAt, 'string');
  assert.equal(typeof row.updatedAt, 'string');

  const otherRow = findBook(books, Number(other.id));
  assert.ok(otherRow);
  assert.equal(otherRow.chapterCount, 1);
  assert.equal(otherRow.doneChapterCount, 0);

  // 单书统计（GET /api/books/[id]/stats 的 doneChapterCount）口径与之一致：
  // 复用 repo 暴露的 listChapters，避免在测试里复制 SQL。
  const doneFromRepo = listChapters(bookId).filter(
    (chapter) => String(chapter.status) === 'final',
  ).length;
  assert.equal(doneFromRepo, row.doneChapterCount, 'stats 口径应与 doneChapterCount 一致');
  assert.equal(doneFromRepo, 1);
});

test('空书（无章节）的 chapterCount 与 doneChapterCount 都是 0', (t) => {
  freshDb(t);

  const empty = createBook({ title: '空书' });
  const row = findBook(listBooks(), Number(empty.id));
  assert.ok(row, '未找到刚建的空书');
  assert.equal(row.chapterCount, 0);
  assert.equal(row.doneChapterCount, 0);
  assert.equal(listChapters(Number(empty.id)).length, 0);
});
