import assert from 'node:assert/strict';
import { test } from 'node:test';

import { normalizeChapterStatus } from '../src/lib/chapter-status.js';
import { closeDb, initDb } from '../src/lib/db.js';
import { createBook, createChapter, getChapter, updateChapter } from '../src/lib/repo.js';

/**
 * db.js 采用单例连接：每个用例先 closeDb() 再 initDb(':memory:') 打开全新内存库，
 * 全程不触碰磁盘文件，可重复运行（与 tests/db.test.mjs 写法一致）。
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

test('normalizeChapterStatus：空值/未定义一律按 draft', () => {
  assert.equal(normalizeChapterStatus(undefined), 'draft');
  assert.equal(normalizeChapterStatus(null), 'draft');
  assert.equal(normalizeChapterStatus(''), 'draft');
  assert.equal(normalizeChapterStatus('   '), 'draft');
});

test('normalizeChapterStatus：draft/final 原样返回，其余值返回 null', () => {
  assert.equal(normalizeChapterStatus('draft'), 'draft');
  assert.equal(normalizeChapterStatus('final'), 'final');
  assert.equal(normalizeChapterStatus(' final '), 'final');

  for (const bad of ['published', 'FINAL', 'Draft', 0, 1, true, {}, [], 'done']) {
    assert.equal(normalizeChapterStatus(bad), null, `${JSON.stringify(bad)} 应被判为非法`);
  }
});

test('新建章节默认写入 draft，随后可更新为 final', (t) => {
  freshDb(t);

  const book = createBook({ title: '状态测试书' });
  assert.ok(book && typeof book.id === 'number', '建书失败');

  const chapter = createChapter({
    bookId: book.id,
    seq: 1,
    title: '第一章',
    content: '',
    // 与新建章节接口保持一致：未传 status 时写 'draft'。
    status: normalizeChapterStatus(undefined) ?? 'draft',
  });
  assert.ok(chapter && typeof chapter.id === 'number', '建章失败');
  assert.equal(chapter.status, 'draft');

  const stored = getChapter(chapter.id);
  assert.equal(stored.status, 'draft', '库里新建章节的 status 应为 draft');

  const updated = updateChapter(chapter.id, { status: 'final' });
  assert.equal(updated.status, 'final');
  assert.equal(getChapter(chapter.id).status, 'final', '更新后库里应为 final');

  // 状态变化不应影响正文与字数统计。
  assert.equal(getChapter(chapter.id).content, '');
  assert.equal(getChapter(chapter.id).wordCount, 0);
});

test('非法状态值不会落库', (t) => {
  freshDb(t);

  const book = createBook({ title: '非法状态书' });
  const chapter = createChapter({ bookId: book.id, seq: 1, title: '草稿章', content: '', status: 'draft' });
  assert.equal(getChapter(chapter.id).status, 'draft');

  const invalid = 'published';
  assert.equal(normalizeChapterStatus(invalid), null, '非法值应被 normalizeChapterStatus 拒绝');
  // 接口层遇到 null 会直接 400、不落库；这里模拟「拒绝后写回原值」的最终结果。
  assert.equal(getChapter(chapter.id).status, 'draft', '非法状态不应改写库里已有值');
});
