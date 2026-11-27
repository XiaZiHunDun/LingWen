/**
 * 复制作品单测：命名规则 / 字段一致性 / 副本与原书解耦。
 * 运行：pnpm test（node:test）
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import { closeDb, getDb, initDb } from '../src/lib/db.js';
import {
  addBible,
  createBook,
  createChapter,
  listBible,
  listChapters,
  listOutlines,
  replaceOutlines,
  updateChapter,
} from '../src/lib/repo.js';
import { NotFoundError, duplicateBook, generateCopyName } from '../src/lib/book-copy.js';
import { countWords } from '../src/lib/wordcount.js';

/** 每个用例都用全新的内存库，互不影响。 */
function freshDb() {
  closeDb();
  initDb(':memory:');
}

/**
 * 造一本「有类型 / 简介 / 风格 + 2 章 + 2 条大纲 + 1 条设定」的书。
 * @returns {number} 书 id
 */
function seedBook() {
  const book = createBook({
    title: '长夜行',
    genre: '玄幻',
    summary: '一个关于长夜与灯的故事。',
    style: '冷峻短句',
  });
  const bookId = Number(book.id);

  replaceOutlines(bookId, [
    { seq: 1, title: '第一卷 起风', summary: '主角出场', status: 'draft' },
    { seq: 2, title: '第二卷 落雪', summary: '势力登场', status: 'draft' },
  ]);
  addBible({ bookId, category: '人物', title: '沈夜', content: '主角，提灯者。' });

  const chapters = [
    { title: '第一章 灯', content: '夜里有一盏灯。灯下有人。', summary: '开场', status: 'final' },
    { title: '第二章 雪', content: '雪落在长街，脚步声渐远。', summary: '转折', status: 'draft' },
  ];
  chapters.forEach((item, index) => {
    createChapter({
      bookId,
      seq: index + 1,
      title: item.title,
      content: item.content,
      summary: item.summary,
      status: item.status,
      wordCount: countWords(item.content),
    });
  });
  return bookId;
}

test('generateCopyName：首个副本加（副本）', () => {
  assert.equal(generateCopyName('长夜行', []), '长夜行（副本）');
  assert.equal(generateCopyName('长夜行'), '长夜行（副本）');
  assert.equal(generateCopyName('长夜行', ['别的书']), '长夜行（副本）');
});

test('generateCopyName：已存在同名副本时依次用（副本 2）（副本 3）', () => {
  assert.equal(generateCopyName('长夜行', ['长夜行', '长夜行（副本）']), '长夜行（副本 2）');
  assert.equal(
    generateCopyName('长夜行', ['长夜行', '长夜行（副本）', '长夜行（副本 2）']),
    '长夜行（副本 3）',
  );
});

test('generateCopyName：结果永不与已有书名重复', () => {
  const existing = ['长夜行', '长夜行（副本）', '长夜行（副本 2）', '长夜行（副本 3）'];
  const name = generateCopyName('长夜行', existing);
  assert.equal(name, '长夜行（副本 4）');
  assert.equal(existing.includes(name), false);
});

test('duplicateBook：书籍字段 / 章节 / 大纲 / 设定逐项一致', () => {
  freshDb();
  const sourceId = seedBook();
  const source = listChapters(sourceId);

  const result = duplicateBook(sourceId);
  assert.equal(result.chapters, 2);
  assert.equal(result.outlines, 2);
  assert.equal(result.bible, 1);
  assert.equal(result.title, '长夜行（副本）');

  const db = getDb();
  const copy = db.prepare('SELECT * FROM books WHERE id = ?').get(result.id);
  assert.equal(copy.title, '长夜行（副本）');
  assert.equal(copy.genre, '玄幻');
  assert.equal(copy.summary, '一个关于长夜与灯的故事。');
  assert.equal(copy.style, '冷峻短句');
  assert.notEqual(Number(copy.id), sourceId);

  const copiedChapters = listChapters(Number(result.id));
  assert.equal(copiedChapters.length, source.length);
  copiedChapters.forEach((chapter, index) => {
    const original = source[index];
    assert.equal(chapter.seq, original.seq);
    assert.equal(chapter.title, original.title);
    assert.equal(chapter.content, original.content);
    assert.equal(chapter.summary, original.summary);
    assert.equal(chapter.status, original.status);
    // 字数沿用 countWords 口径
    assert.equal(chapter.wordCount, countWords(String(original.content)));
    assert.equal(chapter.wordCount, original.wordCount);
    assert.notEqual(chapter.id, original.id);
  });

  const copiedOutlines = listOutlines(Number(result.id));
  const sourceOutlines = listOutlines(sourceId);
  assert.equal(copiedOutlines.length, sourceOutlines.length);
  copiedOutlines.forEach((outline, index) => {
    const original = sourceOutlines[index];
    assert.equal(outline.seq, original.seq);
    assert.equal(outline.title, original.title);
    assert.equal(outline.summary, original.summary);
    assert.equal(outline.status, original.status);
  });

  const copiedBible = listBible(Number(result.id));
  const sourceBible = listBible(sourceId);
  assert.equal(copiedBible.length, sourceBible.length);
  assert.equal(copiedBible[0].category, sourceBible[0].category);
  assert.equal(copiedBible[0].title, sourceBible[0].title);
  assert.equal(copiedBible[0].content, sourceBible[0].content);

  // 副本不改动原书统计：原书仍是 2 章
  assert.equal(listChapters(sourceId).length, 2);
  closeDb();
});

test('duplicateBook：副本与原书解耦（改/删副本章节不影响原书）', () => {
  freshDb();
  const sourceId = seedBook();
  const sourceBefore = listChapters(sourceId);
  const { id: copyId } = duplicateBook(sourceId);

  const copyChapters = listChapters(Number(copyId));
  const target = copyChapters[0];

  // 改副本第一章
  updateChapter(Number(target.id), { title: '改写后的标题', content: '完全换掉的正文内容。' });
  const sourceAfterEdit = listChapters(sourceId);
  assert.equal(sourceAfterEdit.length, sourceBefore.length);
  assert.equal(sourceAfterEdit[0].title, sourceBefore[0].title);
  assert.equal(sourceAfterEdit[0].content, sourceBefore[0].content);
  assert.equal(sourceAfterEdit[0].wordCount, sourceBefore[0].wordCount);

  // 删副本第一章（直接删行，验证两本书的章节互不影响）
  getDb().prepare('DELETE FROM chapters WHERE id = ?').run(Number(target.id));
  assert.equal(listChapters(Number(copyId)).length, 1);
  assert.equal(listChapters(sourceId).length, 2);

  // 再复制一次应得到「副本 2」
  const second = duplicateBook(sourceId);
  assert.equal(second.title, '长夜行（副本 2）');
  closeDb();
});

test('duplicateBook：原书不存在时抛 NotFoundError', () => {
  freshDb();
  assert.throws(
    () => duplicateBook(9999),
    (error) => error instanceof NotFoundError && error.code === 'NOT_FOUND',
  );
  closeDb();
});
