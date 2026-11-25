import assert from 'node:assert/strict';
import { test } from 'node:test';

import { closeDb, getDb, initDb } from '../src/lib/db.js';

/**
 * db.js 采用单例连接：initDb(':memory:') 在连接已存在且路径一致时会复用旧连接，
 * 因此每个用例先 closeDb() 释放，再 initDb(':memory:') 打开一个全新的内存库，
 * 用例结束后再 closeDb()。全程不触碰任何磁盘文件，可重复运行。
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

test('initDb 打开内存库并建好五张表', (t) => {
  const db = freshDb(t);

  const tables = db
    .prepare("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    .all()
    .map((row) => row.name);

  for (const name of ['books', 'bible', 'outlines', 'chapters', 'llm_logs']) {
    assert.ok(tables.includes(name), `缺少表 ${name}，实际表：${tables.join(', ')}`);
  }
});

test('PRAGMA table_list 也能看到五张表', (t) => {
  const db = freshDb(t);

  const names = db
    .prepare('PRAGMA table_list')
    .all()
    .map((row) => row.name);

  for (const name of ['books', 'bible', 'outlines', 'chapters', 'llm_logs']) {
    assert.ok(names.includes(name), `PRAGMA table_list 缺少表 ${name}`);
  }
});

test('getDb 返回当前连接，未初始化时抛出清晰错误', (t) => {
  closeDb();
  assert.throws(() => getDb(), /尚未初始化/);

  const db = initDb(':memory:');
  t.after(() => closeDb());
  assert.equal(getDb(), db);
  assert.equal(getDb().open, true);

  closeDb();
  assert.throws(() => getDb(), /尚未初始化/);
});

test('foreign_keys 已开启', (t) => {
  const db = freshDb(t);
  assert.equal(db.pragma('foreign_keys', { simple: true }), 1);
});

test('插入一本书后能原样读回', (t) => {
  const db = freshDb(t);

  const info = db
    .prepare(
      `INSERT INTO books (title, genre, summary, style, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?)`,
    )
    .run('长夜将明', '玄幻', '少年持灯夜行。', '第三人称', '2024-01-01T00:00:00.000Z', '2024-01-02T00:00:00.000Z');

  assert.equal(info.changes, 1);
  const id = Number(info.lastInsertRowid);
  assert.ok(id > 0);

  const row = db.prepare('SELECT * FROM books WHERE id = ?').get(id);
  assert.ok(row, `未读回 id=${id} 的书`);
  assert.equal(row.id, id);
  assert.equal(row.title, '长夜将明');
  assert.equal(row.genre, '玄幻');
  assert.equal(row.summary, '少年持灯夜行。');
  assert.equal(row.style, '第三人称');
  assert.equal(row.created_at, '2024-01-01T00:00:00.000Z');
  assert.equal(row.updated_at, '2024-01-02T00:00:00.000Z');

  // 再插入一本，id 自增且互不覆盖。
  const second = db.prepare('INSERT INTO books (title) VALUES (?)').run('归墟');
  assert.equal(Number(second.lastInsertRowid), id + 1);
  assert.equal(db.prepare('SELECT COUNT(*) AS c FROM books').get().c, 2);
});

test('删除 book 会级联删除其 bible 行', (t) => {
  const db = freshDb(t);
  assert.equal(db.pragma('foreign_keys', { simple: true }), 1, 'foreign_keys 未开启则级联不会生效');

  const bookId = Number(
    db.prepare('INSERT INTO books (title) VALUES (?)').run('级联测试').lastInsertRowid,
  );
  db.prepare('INSERT INTO bible (book_id, category, title, content) VALUES (?, ?, ?, ?)').run(
    bookId,
    '人物',
    '林砚',
    '持灯人。',
  );
  db.prepare('INSERT INTO bible (book_id, category, title, content) VALUES (?, ?, ?, ?)').run(
    bookId,
    '地点',
    '青灯城',
    '不夜的城。',
  );
  assert.equal(db.prepare('SELECT COUNT(*) AS c FROM bible WHERE book_id = ?').get(bookId).c, 2);

  const deleted = db.prepare('DELETE FROM books WHERE id = ?').run(bookId);
  assert.equal(deleted.changes, 1);

  assert.equal(
    db.prepare('SELECT COUNT(*) AS c FROM bible WHERE book_id = ?').get(bookId).c,
    0,
    'books 删除后 bible 子行应被级联清理',
  );
  assert.equal(db.prepare('SELECT COUNT(*) AS c FROM bible').get().c, 0);
});

test('chapters 的 word_count 未显式给值时默认为 0', (t) => {
  const db = freshDb(t);

  const bookId = Number(
    db.prepare('INSERT INTO books (title) VALUES (?)').run('字数默认').lastInsertRowid,
  );

  const inserted = db
    .prepare('INSERT INTO chapters (book_id, seq, title, content) VALUES (?, ?, ?, ?)')
    .run(bookId, 1, '第一章', '风雨如晦，鸡鸣不已。');
  const id = Number(inserted.lastInsertRowid);

  const row = db.prepare('SELECT * FROM chapters WHERE id = ?').get(id);
  assert.ok(row);
  assert.equal(row.word_count, 0, `word_count 默认值应为 0，实际 ${row.word_count}`);
  assert.equal(typeof row.word_count, 'number');
  assert.equal(row.title, '第一章');

  // 其余子表的默认值/可空列也不应阻塞插入。
  db.prepare('INSERT INTO outlines (book_id, seq, title) VALUES (?, ?, ?)').run(bookId, 1, '开端');
  db.prepare('INSERT INTO llm_logs (book_id, kind, prompt, response, elapsed_ms) VALUES (?, ?, ?, ?, ?)').run(
    bookId,
    'outline',
    'p',
    'r',
    12,
  );
  assert.equal(db.prepare('SELECT COUNT(*) AS c FROM outlines').get().c, 1);
  assert.equal(db.prepare('SELECT COUNT(*) AS c FROM llm_logs').get().c, 1);
});

test('重复调用 initDb 复用同一内存连接，closeDb 可重复调用', (t) => {
  closeDb();
  const first = initDb(':memory:');
  const second = initDb(':memory:');
  assert.equal(first, second, '相同路径应复用同一连接');
  first.prepare('INSERT INTO books (title) VALUES (?)').run('复用');
  assert.equal(second.prepare('SELECT COUNT(*) AS c FROM books').get().c, 1);

  closeDb();
  closeDb(); // 幂等，不应抛错
  assert.throws(() => getDb(), /尚未初始化/);
});
